// M030 independent diagnostic EA. OBSERVATION ONLY.
// No trade library, no OrderSend, no account access and no broker connection.
// Runs only in Strategy Tester and writes a CSV of completed-M1 decisions.
// Synthetic/real-tick mode and server clock offsets must be documented separately.
#property strict
#property version "1.00"

input string RunId = "M030-stage1a";
input string OutputName = "m030_decisions.csv";

int handle = INVALID_HANDLE;
datetime lastBoundary = 0;
const int KPER = 21, DPER = 7, SLOW = 7;
const int HISTORY = 512;

struct Bar {
  datetime start;
  double open, high, low, close;
};
bool GetBars(ENUM_TIMEFRAMES tf, Bar &result[]) {
  MqlRates rates[];
  ArraySetAsSeries(rates, false);
  int count = CopyRates(_Symbol, tf, 1, HISTORY, rates); // completed only
  if(count < 40) return false;
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
  if(_Symbol!="EURUSD") {
    Print("M030 DENIED: frozen first symbol must be EURUSD");
    return INIT_FAILED;
  }
  handle=FileOpen(OutputName,FILE_CSV|FILE_WRITE|FILE_ANSI|FILE_COMMON,',');
  if(handle==INVALID_HANDLE) return INIT_FAILED;
  FileWrite(handle,"run_id","symbol","server_boundary","m1_source_open",
            "m5_source_open","m1_k","m1_d","m5_k","m5_d",
            "ema","atr","signal","reason");
  return INIT_SUCCEEDED;
}
void OnDeinit(const int reason) {
  if(handle!=INVALID_HANDLE) FileClose(handle);
}
void OnTick() {
  datetime boundary=iTime(_Symbol,PERIOD_M1,0);
  if(boundary==0 || boundary==lastBoundary) return;
  lastBoundary=boundary;
  Bar m1[],m5[];
  if(!GetBars(PERIOD_M1,m1)||!GetBars(PERIOD_M5,m5)) return;
  double k1,d1,k5,d5; bool low1,high1,low5,high5;
  if(!Stoch(m1,k1,d1,low1,high1) || !Stoch(m5,k5,d5,low5,high5)) return;
  double ema=Ema(m1,7),atr=Atr(m5,14);
  int n=ArraySize(m1);
  string signal="NONE",reason="NO_SIGNAL";
  // Preserve the original recent-extreme check, NOT a fresh cross.
  bool buy=k5>d5 && low1 && k1>d1;
  bool sell=k5<d5 && high1 && k1<d1;
  if(buy && m1[n-1].close>ema && m1[n-1].close>m1[n-1].open) {
    signal="BUY"; reason="ENTRY_CONDITIONS";
  } else if(sell && m1[n-1].close<ema && m1[n-1].close<m1[n-1].open) {
    signal="SELL";reason="ENTRY_CONDITIONS";
  } else if(buy || sell) reason="EMA_CANDLE_FILTER";
  FileWrite(handle,RunId,_Symbol,TimeToString(boundary,TIME_DATE|TIME_SECONDS),
            TimeToString(m1[n-1].start,TIME_DATE|TIME_SECONDS),
            TimeToString(m5[ArraySize(m5)-1].start,TIME_DATE|TIME_SECONDS),
            DoubleToString(k1,12),DoubleToString(d1,12),
            DoubleToString(k5,12),DoubleToString(d5,12),
            DoubleToString(ema,12),DoubleToString(atr,12),signal,reason);
  FileFlush(handle);
}
