// M030 Stage 1H — INDEPENDENT BAR/CLOCK DISCOVERY. NO ORDER CODE.
// Tester-only diagnostic; all timestamps below are raw MT5 SERVER time.
// No UTC assumption, no account calls and no strategy indicator calculations.
#property strict
#property version "1.00"

input string RunId = "M030-1H-UNSET";
input string OutputName = "m030_clock_probe.csv";
// Broad *server-local* research envelope, deliberately not called UTC.
// Must be separately reviewed to include ALL candidate UTC offsets.
input datetime ServerEnvelopeStart = 0;
input datetime ServerEnvelopeEnd = 0;
input int MaximumRows = 10000;

int csv_handle = INVALID_HANDLE;
int emitted_rows = 0;
datetime last_m1_boundary = 0;
datetime last_m5_source = 0;
bool initialized_m5 = false;

struct ObservedBar {
  datetime source_open;
  double open, high, low, close;
};

bool LatestCompleted(ENUM_TIMEFRAMES tf, datetime expected_open, ObservedBar &bar) {
  MqlRates rates[];
  ArraySetAsSeries(rates,false);
  if(CopyRates(_Symbol,tf,1,1,rates)!=1) return false;
  if(rates[0].time!=expected_open) {
    PrintFormat("M030 1H DENIED: %d expected %s but saw %s",
      (int)tf,TimeToString(expected_open,TIME_DATE|TIME_SECONDS),
      TimeToString(rates[0].time,TIME_DATE|TIME_SECONDS));
    return false;
  }
  bar.source_open=rates[0].time;
  bar.open=rates[0].open;
  bar.high=rates[0].high;
  bar.low=rates[0].low;
  bar.close=rates[0].close;
  return true;
}

bool EmitBar(string timeframe, datetime boundary, datetime observed_tick,
             ObservedBar &bar) {
  if(emitted_rows>=MaximumRows) {
    Print("M030 1H DENIED: row cap reached; stopping without truncation claim");
    return false;
  }
  if(bar.source_open>=boundary || observed_tick<boundary) {
    Print("M030 1H DENIED: bar was not completed at recorded boundary");
    return false;
  }
  FileWrite(csv_handle,RunId,_Symbol,timeframe,
    TimeToString(boundary,TIME_DATE|TIME_SECONDS),
    TimeToString(observed_tick,TIME_DATE|TIME_SECONDS),
    TimeToString(bar.source_open,TIME_DATE|TIME_SECONDS),
    DoubleToString(bar.open,_Digits),DoubleToString(bar.high,_Digits),
    DoubleToString(bar.low,_Digits),DoubleToString(bar.close,_Digits));
  emitted_rows++;
  return true;
}

int OnInit() {
  if(!MQLInfoInteger(MQL_TESTER)) {
    Print("M030 1H DENIED: tester context only");
    return INIT_FAILED;
  }
  if(_Symbol!="EURUSD" || RunId=="" || RunId=="M030-1H-UNSET" ||
     ServerEnvelopeStart<=0 || ServerEnvelopeEnd<=ServerEnvelopeStart ||
     ServerEnvelopeEnd-ServerEnvelopeStart>7*86400 ||
     MaximumRows<2 || MaximumRows>20000 || OutputName=="") {
    Print("M030 1H DENIED: explicit frozen inputs required");
    return INIT_FAILED;
  }
  if(FileIsExist(OutputName,FILE_COMMON)) {
    Print("M030 1H DENIED: evidence file already exists");
    return INIT_FAILED;
  }
  csv_handle=FileOpen(OutputName,FILE_CSV|FILE_WRITE|FILE_ANSI|FILE_COMMON,',');
  if(csv_handle==INVALID_HANDLE) {
    Print("M030 1H DENIED: unable to open immutable output");
    return INIT_FAILED;
  }
  FileWrite(csv_handle,"run_id","symbol","timeframe",
            "server_m1_boundary","server_observed_tick","server_bar_open",
            "open","high","low","close");
  FileFlush(csv_handle);
  return INIT_SUCCEEDED;
}

void OnDeinit(const int reason) {
  if(csv_handle!=INVALID_HANDLE) {
    FileFlush(csv_handle);
    FileClose(csv_handle);
  }
  PrintFormat("M030 1H stopped reason=%d rows=%d",reason,emitted_rows);
}

void OnTick() {
  datetime boundary=iTime(_Symbol,PERIOD_M1,0);
  if(boundary==0 || boundary==last_m1_boundary) return;
  if(boundary<ServerEnvelopeStart || boundary>=ServerEnvelopeEnd) return;

  // First tick after new M1 open may arrive seconds later.
  datetime observed=TimeCurrent();
  if(observed<boundary) {
    Print("M030 1H DENIED: observed tick before boundary");
    ExpertRemove();
    return;
  }
  if(last_m1_boundary!=0 && boundary!=last_m1_boundary+60) {
    Print("M030 1H DENIED: missing M1 boundary within research envelope");
    ExpertRemove();
    return;
  }
  datetime m5_open=(datetime)(((long)boundary/300)*300-300);
  ObservedBar m1,m5;
  if(!LatestCompleted(PERIOD_M1,boundary-60,m1) ||
     !LatestCompleted(PERIOD_M5,m5_open,m5)) {
    Print("M030 1H DENIED: unavailable, stale or uncompleted native bars");
    ExpertRemove();
    return;
  }
  if(!EmitBar("M1",boundary,observed,m1)) {
    ExpertRemove();
    return;
  }
  if(!initialized_m5 || m5.source_open!=last_m5_source) {
    if(initialized_m5 && m5.source_open!=last_m5_source+300) {
      Print("M030 1H DENIED: missing M5 source bar");
      ExpertRemove();
      return;
    }
    if(!EmitBar("M5",boundary,observed,m5)) {
      ExpertRemove();
      return;
    }
    last_m5_source=m5.source_open;
    initialized_m5=true;
  }
  last_m1_boundary=boundary;
  FileFlush(csv_handle);
}
