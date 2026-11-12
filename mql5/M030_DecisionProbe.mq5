// M030 independent diagnostic EA. OBSERVATION ONLY.
// No trade library, no OrderSend, no account access and no broker connection.
// Runs only in Strategy Tester and writes a CSV of completed-M1 decisions.
// Synthetic/real-tick mode and server clock offsets must be documented separately.
#property strict
#property version "1.00"

input string RunId = "M030-stage1a";
input string OutputName = "m030_decisions.csv";
// Must be set to the exact earliest source-bar open in Python's dataset.
// Default invalid: tester refuses to run without an explicit seed.
// These timestamps are SERVER clock bar opens, not UTC. Set both from
// independently verified MT5-to-UTC mapping; default zero refuses to start.
input datetime M1SourceStartServer = 0;
input datetime M5SourceStartServer = 0;
input datetime ComparisonStart = D'2026.09.10 00:00';
input datetime ComparisonEnd = D'2026.09.11 00:00';
// ComparisonStart/End are UTC labels. Never infer server clock from Kenya.
// The sentinel requires an independently established historical server offset.
input int VerifiedServerUtcOffsetMinutes = 99999;
datetime server_sample_start=0, server_sample_end=0;

int handle = INVALID_HANDLE;
int audit_handle = INVALID_HANDLE;
input string BarAuditOutputName = "m030_bar_audit.csv";
input bool EmitBarAudit = false;
bool bar_audit_done = false;
datetime lastBoundary = 0;
const int KPER = 21, DPER = 7, SLOW = 7;


struct Bar {
  datetime start;
  double open, high, low, close;
};
bool GetBars(ENUM_TIMEFRAMES tf, datetime expected_start, Bar &result[]) {
  MqlRates rates[];
  ArraySetAsSeries(rates, false);
  // Complete source history; never seed EMA at an arbitrary 512-bar cutoff.
  int count = CopyRates(_Symbol, tf, expected_start, TimeCurrent(), rates);
  if(count <= 0) return false;
  // CopyRates range is inclusive by bar OPEN. Exclude the currently
  // forming candle; assert the initial source candle instead of truncating.
  datetime current_open = iTime(_Symbol,tf,0);
  if(current_open <= 0) return false;
  if(rates[count-1].time >= current_open) count--;
  if(count < 40 || rates[0].time != expected_start) {
    PrintFormat("M030 MISSING PREFIX tf=%d expected=%s first=%s count=%d",
                (int)tf, TimeToString(expected_start), 
                count>0?TimeToString(rates[0].time):"NONE", count);
    return false;
  }
  for(int i=1;i<count;i++) {
    if(rates[i].time <= rates[i-1].time || rates[i].time >= current_open) {
      Print("M030 DENIED: duplicate, reversed or unclosed history bars");
      return false;
    }
  }
  ArrayResize(result, count);
  for(int i=0;i<count;i++) {
    result[i].start=rates[i].time;
    result[i].open=rates[i].open;
    result[i].high=rates[i].high;
    result[i].low=rates[i].low;
    result[i].close=rates[i].close;
  }
  return true;
}
// Exact independent production formula: high/low extrema over KPER,
// slowing = sum(close-lowest)/sum(highest-lowest), D = SMA of main K.
// Python initializes pre-warmup K/D elements to zero.
bool Stoch(Bar &bars[], double &k, double &d, bool &recentLow, bool &recentHigh) {
  int n=ArraySize(bars);
  if(n<KPER+DPER+SLOW) return false;
  double highest[], lowest[], mainK[];
  ArrayResize(highest,n); ArrayResize(lowest,n); ArrayResize(mainK,n);
  ArrayInitialize(highest,0.0); ArrayInitialize(lowest,0.0); ArrayInitialize(mainK,0.0);
  for(int i=KPER-1;i<n;i++) {
    double hi=bars[i].high, lo=bars[i].low;
    for(int j=i-KPER+1;j<=i;j++) {
      if(bars[j].high>hi) hi=bars[j].high;
      if(bars[j].low<lo) lo=bars[j].low;
    }
    highest[i]=hi; lowest[i]=lo;
  }
  for(int i=KPER+SLOW-2;i<n;i++) {
    double lowSum=0,rangeSum=0;
    for(int j=i-SLOW+1;j<=i;j++) {
      lowSum+=bars[j].close-lowest[j];
      rangeSum+=highest[j]-lowest[j];
    }
    mainK[i]=(rangeSum==0.0?100.0:100.0*lowSum/rangeSum);
  }
  k=mainK[n-1]; d=0;
  for(int j=n-DPER;j<n;j++) d+=mainK[j];
  d/=DPER;
  recentLow=false; recentHigh=false;
  for(int j=MathMax(0,n-10);j<n;j++) {
    if(mainK[j]<20.0) recentLow=true;
    if(mainK[j]>80.0) recentHigh=true;
  }
  return true;
}
double Ema(Bar &bars[], int period) {
  double value=bars[0].close, alpha=2.0/(period+1.0);
  for(int i=1;i<ArraySize(bars);i++) value=alpha*bars[i].close+(1-alpha)*value;
  return value;
}
double Atr(Bar &bars[], int period) {
  int n=ArraySize(bars);
  if(n<period+1) return 0.0;
  double total=0;
  for(int i=n-period;i<n;i++) {
    double tr=bars[i].high-bars[i].low;
    if(i>0) {
      tr=MathMax(tr,MathAbs(bars[i].high-bars[i-1].close));
      tr=MathMax(tr,MathAbs(bars[i].low-bars[i-1].close));
    }
    total+=tr;
  }
  return total/period;
}
int OnInit() {
  if(!MQLInfoInteger(MQL_TESTER)) {
    Print("M030 DENIED: EA may only run in Strategy Tester");
    return INIT_FAILED;
  }
  if(VerifiedServerUtcOffsetMinutes==99999 ||
     VerifiedServerUtcOffsetMinutes < -840 || VerifiedServerUtcOffsetMinutes > 840) {
    Print("M030 DENIED: independently verified historical server offset required");
    return INIT_FAILED;
  }
  server_sample_start=ComparisonStart+VerifiedServerUtcOffsetMinutes*60;
  server_sample_end=ComparisonEnd+VerifiedServerUtcOffsetMinutes*60;
  if(M1SourceStartServer<=0 || M5SourceStartServer<=0 ||
     M1SourceStartServer>=server_sample_start ||
     M5SourceStartServer>=server_sample_start ||
     ComparisonStart>=ComparisonEnd) {
    Print("M030 DENIED: missing history start or invalid frozen date window");
    return INIT_FAILED;
  }
  if(_Symbol!="EURUSD") {
    Print("M030 DENIED: frozen first symbol must be EURUSD");
    return INIT_FAILED;
  }
  if(EmitBarAudit && (BarAuditOutputName==OutputName ||
      FileIsExist(BarAuditOutputName,FILE_COMMON))) {
    Print("M030 DENIED: audit path collides or already exists");
    return INIT_FAILED;
  }
  if(FileIsExist(OutputName,FILE_COMMON)) {
    Print("M030 DENIED: output exists; choose an unused evidence file name");
    return INIT_FAILED;
  }
  handle=FileOpen(OutputName,FILE_CSV|FILE_WRITE|FILE_ANSI|FILE_COMMON,',');
  if(handle==INVALID_HANDLE) return INIT_FAILED;
  if(EmitBarAudit) {
    audit_handle=FileOpen(BarAuditOutputName,FILE_CSV|FILE_WRITE|FILE_ANSI|FILE_COMMON,',');
    if(audit_handle==INVALID_HANDLE) { FileClose(handle);handle=INVALID_HANDLE;return INIT_FAILED; }
    FileWrite(audit_handle,"run_id","symbol","timeframe","server_bar_open",
              "open","high","low","close");
  }
  FileWrite(handle,"run_id","symbol","server_boundary","m1_source_open",
            "m5_source_open","m1_k","m1_d","m5_k","m5_d",
            "ema","atr","signal","reason");
  return INIT_SUCCEEDED;
}
void OnDeinit(const int reason) {
  if(handle!=INVALID_HANDLE) FileClose(handle);
  if(audit_handle!=INVALID_HANDLE) FileClose(audit_handle);
}
// The last 48 bars contain more than the 21+7+7 stochastic
// dependencies and the ten-entry-K extreme lookback. The full Python
// source prefix is used exactly once to seed EMA from its earliest M1 close.
// We do NOT truncate the EMA seed to the last 48 bars.
const int WINDOW_BARS = 48;
Bar m1_window[], m5_window[];
datetime last_m1_open=0, last_m5_open=0;
double incremental_ema=0;
bool state_ready=false;

void TailWindow(Bar &source[], Bar &dest[]) {
  int count=ArraySize(source);
  int start=MathMax(0,count-WINDOW_BARS);
  ArrayResize(dest,count-start);
  for(int i=start;i<count;i++) dest[i-start]=source[i];
}

void AppendWindow(Bar &bars[], const Bar &next_bar) {
  int count=ArraySize(bars);
  if(count<WINDOW_BARS) {
    ArrayResize(bars,count+1);
    bars[count]=next_bar;
    return;
  }
  for(int i=1;i<count;i++) bars[i-1]=bars[i];
  bars[count-1]=next_bar;
}

bool ReadNewestCompleted(ENUM_TIMEFRAMES tf, datetime expected_open, Bar &out) {
  MqlRates latest[];
  ArraySetAsSeries(latest,false);
  if(CopyRates(_Symbol,tf,1,1,latest)!=1) return false;
  if(latest[0].time!=expected_open) {
    PrintFormat("M030 DENIED: newest completed %d expected %s got %s",
      (int)tf,TimeToString(expected_open),TimeToString(latest[0].time));
    return false;
  }
  out.start=latest[0].time;
  out.open=latest[0].open;
  out.high=latest[0].high;
  out.low=latest[0].low;
  out.close=latest[0].close;
  return true;
}

void WriteInitialAudit(Bar &m1[], Bar &m5[]) {
  if(!EmitBarAudit || bar_audit_done) return;
  for(int i=0;i<ArraySize(m1);i++)
    FileWrite(audit_handle,RunId,_Symbol,"M1",
              TimeToString(m1[i].start,TIME_DATE|TIME_SECONDS),
              DoubleToString(m1[i].open,_Digits),DoubleToString(m1[i].high,_Digits),
              DoubleToString(m1[i].low,_Digits),DoubleToString(m1[i].close,_Digits));
  for(int i=0;i<ArraySize(m5);i++)
    FileWrite(audit_handle,RunId,_Symbol,"M5",
              TimeToString(m5[i].start,TIME_DATE|TIME_SECONDS),
              DoubleToString(m5[i].open,_Digits),DoubleToString(m5[i].high,_Digits),
              DoubleToString(m5[i].low,_Digits),DoubleToString(m5[i].close,_Digits));
  FileFlush(audit_handle);
  bar_audit_done=true;
}

bool InitializeState(datetime boundary, datetime expected_m5_open) {
  Bar m1_full[],m5_full[];
  if(!GetBars(PERIOD_M1,M1SourceStartServer,m1_full) ||
     !GetBars(PERIOD_M5,M5SourceStartServer,m5_full)) return false;
  int n1=ArraySize(m1_full),n5=ArraySize(m5_full);
  if(n1<WINDOW_BARS || n5<WINDOW_BARS ||
     m1_full[n1-1].start!=boundary-60 ||
     m5_full[n5-1].start!=expected_m5_open) {
    Print("M030 DENIED: initial completed-prefix alignment/length mismatch");
    return false;
  }
  // Full Python ewm(span=7,adjust=False): first source close is the seed.
  incremental_ema=Ema(m1_full,7);
  WriteInitialAudit(m1_full,m5_full);
  TailWindow(m1_full,m1_window);
  TailWindow(m5_full,m5_window);
  last_m1_open=boundary-60;
  last_m5_open=expected_m5_open;
  state_ready=true;
  return true;
}

bool AdvanceState(datetime boundary, datetime expected_m5_open) {
  Bar bar;
  // Do not accept any missing or duplicated M1 completed boundary.
  if(boundary-60!=last_m1_open+60 ||
     !ReadNewestCompleted(PERIOD_M1,boundary-60,bar)) return false;
  incremental_ema=0.25*bar.close+0.75*incremental_ema;
  AppendWindow(m1_window,bar);
  last_m1_open=bar.start;

  if(expected_m5_open==last_m5_open) return true;
  if(expected_m5_open!=last_m5_open+300 ||
     !ReadNewestCompleted(PERIOD_M5,expected_m5_open,bar)) return false;
  AppendWindow(m5_window,bar);
  last_m5_open=bar.start;
  return true;
}

void OnTick() {
  datetime boundary=iTime(_Symbol,PERIOD_M1,0);
  if(boundary==0 || boundary==lastBoundary) return;
  lastBoundary=boundary;
  if(boundary<server_sample_start || boundary>=server_sample_end) return;

  datetime expected_m5_open=(datetime)(((long)boundary/300)*300-300);
  if(!state_ready) {
    if(!InitializeState(boundary,expected_m5_open)) {
      Print("M030 DENIED: missing/unaligned first full historical prefix");
      ExpertRemove();
      return;
    }
  } else if(!AdvanceState(boundary,expected_m5_open)) {
    Print("M030 DENIED: missing M1/M5 increment or calendar gap");
    ExpertRemove();
    return;
  }

  double k1,d1,k5,d5;
  bool low1,high1,low5,high5;
  if(!Stoch(m1_window,k1,d1,low1,high1) ||
     !Stoch(m5_window,k5,d5,low5,high5)) {
    Print("M030 DENIED: insufficient rolling stochastic state");
    ExpertRemove();
    return;
  }
  double ema=incremental_ema,atr=Atr(m5_window,14);
  int n=ArraySize(m1_window);
  string signal="NONE",reason="NO_SIGNAL";
  // No fresh crossover: preserve Python's latest-K and ten-K-extreme rules.
  bool buy=k5>d5 && low1 && k1>d1;
  bool sell=k5<d5 && high1 && k1<d1;
  if(buy && m1_window[n-1].close>ema &&
     m1_window[n-1].close>m1_window[n-1].open) {
    signal="BUY";reason="ENTRY_CONDITIONS";
  } else if(sell && m1_window[n-1].close<ema &&
            m1_window[n-1].close<m1_window[n-1].open) {
    signal="SELL";reason="ENTRY_CONDITIONS";
  } else if(buy || sell) reason="EMA_CANDLE_FILTER";

  FileWrite(handle,RunId,_Symbol,TimeToString(boundary,TIME_DATE|TIME_SECONDS),
            TimeToString(last_m1_open,TIME_DATE|TIME_SECONDS),
            TimeToString(last_m5_open,TIME_DATE|TIME_SECONDS),
            DoubleToString(k1,12),DoubleToString(d1,12),
            DoubleToString(k5,12),DoubleToString(d5,12),
            DoubleToString(ema,12),DoubleToString(atr,12),signal,reason);
  FileFlush(handle);
}
