// Independent M031 LEAN reference implementation.
// No Mamba2 namespaces or Python/strategy implementation are imported.
#nullable enable

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Data;
using QuantConnect.Orders;
using QuantConnect.Securities;

namespace Mamba2.M031;

public sealed class M031FrozenBaselineAlgorithm : QCAlgorithm
{
    private readonly List<M031Bar> _m1 = new();
    private readonly List<M031Bar> _m5 = new();
    private readonly Dictionary<DateTime, M031Bar> _ask = new();
    private readonly StringBuilder _trace = new();
    private readonly StringBuilder _events = new();
    private readonly Dictionary<int, string> _orderReasons = new();
    private readonly Dictionary<int, int> _positionOrders = new();
    private Symbol _m1Symbol = null!;
    private Symbol _m5Symbol = null!;
    private Symbol _askSymbol = null!;
    private DateTime _sampleStart;
    private DateTime _sampleEnd;
    private int _lastProcessedM1 = -1;
    private decimal? _atr;
    private int _pendingOrderId;
    private int _signalCount;
    private int _boundaryCount;

    private const int KPeriod = 21;
    private const int DPeriod = 7;
    private const int Slowing = 7;
    private const int EmaPeriod = 7;
    private const int AtrPeriod = 14;
    private const decimal Volume = 0.1m;
    private const string Schema = "m030.events.v1";
    private const string ExpectedM1Sha256 = "19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe";
    private const string ExpectedM1AskSha256 = "7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c";
    private const string ExpectedM5Sha256 = "c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9";

    public override void Initialize()
    {
        SetTimeZone(TimeZones.Utc);
        SetStartDate(2025, 8, 25);
        SetEndDate(2026, 9, 11);
        SetCash(10000m);

        M031SourcePaths.M1 = GetParameter("m1_path");
        M031SourcePaths.M1Ask = GetParameter("m1_ask_path");
        M031SourcePaths.M5 = GetParameter("m5_path");
        _sampleStart = DateTime.Parse(GetParameter("sample_start"), CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
        _sampleEnd = DateTime.Parse(GetParameter("sample_end"), CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
        ValidateInputSeal();

        _m1Symbol = AddData<M031M1>("M031_EURUSD_M1", Resolution.Minute, TimeZones.Utc).Symbol;
        _askSymbol = AddData<M031M1Ask>("M031_EURUSD_M1_ASK", Resolution.Minute, TimeZones.Utc).Symbol;
        _m5Symbol = AddData<M031M5>("M031_EURUSD_M5", Resolution.Minute, TimeZones.Utc).Symbol;
        WriteInputManifest();
    }

    public override void OnData(Slice slice)
    {
        // Update all source streams first, then process the M1 completion
        // boundary. This makes M5 available only when EndTime <= boundary.
        if (slice.ContainsKey(_m5Symbol))
            AddM5(slice[_m5Symbol] as M031M5);
        if (slice.ContainsKey(_askSymbol))
            AddAsk(slice[_askSymbol] as M031M1Ask);
        if (!slice.ContainsKey(_m1Symbol))
            return;

        var bar = slice[_m1Symbol] as M031M1;
        if (bar == null || bar.Time <= (_lastProcessedM1 < 0 ? DateTime.MinValue : _m1[_lastProcessedM1].Time))
            return;
        _m1.Add(new M031Bar(bar.Time, bar.EndTime, bar.Open, bar.High, bar.Low, bar.Close, bar.Spread));
        _lastProcessedM1++;

        var boundary = bar.EndTime.ToUniversalTime();
        EmitEvent("M1_CLOSE", boundary, bar.Time, null, null, null, null);
        RefreshAtr();
        var observation = Observe(boundary, bar.Time);
        AppendTrace(observation);

        if (boundary < _sampleStart || boundary > _sampleEnd)
            return;
        _boundaryCount++;
        if (IsBlocked())
            return;
        if (observation.Signal is not ("BUY" or "SELL"))
            return;

        _signalCount++;
        EmitEvent("SIGNAL", boundary, bar.Time, observation.M5SourceOpen, observation.Signal,
            observation.M1K, observation.M1D, observation.M5K, observation.M5D, observation.Ema, observation.Atr);
        var order = MarketOrder(
            Symbol.Create("EURUSD", SecurityType.Forex, Market.Oanda),
            observation.Signal == "BUY" ? Volume : -Volume,
            false,
            "M031|" + observation.Signal);
        _pendingOrderId = order.OrderId;
        _orderReasons[order.OrderId] = observation.Signal;
        EmitEvent("SUBMIT", boundary, bar.Time, observation.M5SourceOpen, observation.Signal,
            observation.M1K, observation.M1D, observation.M5K, observation.M5D, observation.Ema, observation.Atr,
            requestId: order.OrderId);
    }

    public override void OnOrderEvent(OrderEvent orderEvent)
    {
        if (orderEvent.Status == OrderStatus.Filled && _orderReasons.TryGetValue(orderEvent.OrderId, out var side))
        {
            _positionOrders[orderEvent.OrderId] = orderEvent.OrderId;
            _pendingOrderId = 0;
            EmitEvent("FILL", Time, Time - TimeSpan.FromMinutes(1), null, side,
                entryPrice: orderEvent.FillPrice, requestId: orderEvent.OrderId, positionId: orderEvent.OrderId);
            AttachProtectionIfReady(orderEvent.OrderId, side);
        }
        else if (orderEvent.Status == OrderStatus.Canceled || orderEvent.Status == OrderStatus.Invalid)
        {
            _pendingOrderId = 0;
            EmitEvent("REJECT", Time, Time - TimeSpan.FromMinutes(1), null, null,
                requestId: orderEvent.OrderId, reason: orderEvent.Message);
        }
    }

    public override void OnEndOfAlgorithm()
    {
        var summary = new
        {
            schema_version = 1,
            decision_boundaries = _boundaryCount,
            signal_events = _signalCount,
            unresolved_positions = Portfolio.Values.Count(x => x.Invested),
            modeled_costs = new { commission_per_lot_per_side = 0m, slippage_points = 0m, swap = "not_modeled" },
            economic_interpretation = "none; independent comparison trace only"
        };
        ObjectStore.Save("m031/input_manifest.json", BuildManifest());
        ObjectStore.Save("m031/indicator_trace.jsonl", _trace.ToString());
        ObjectStore.Save("m031/events.jsonl", _events.ToString());
        ObjectStore.Save("m031/summary.json", JsonConvert.SerializeObject(summary, Formatting.Indented));
    }

    private void AddM5(M031M5? value)
    {
        if (value == null) return;
        _m5.Add(new M031Bar(value.Time, value.EndTime, value.Open, value.High, value.Low, value.Close, value.Spread));
    }

    private void AddAsk(M031M1Ask? value)
    {
        if (value != null) _ask[value.Time] = new M031Bar(value.Time, value.EndTime, value.Open, value.High, value.Low, value.Close, value.Spread);
    }

    private bool IsBlocked()
    {
        return _pendingOrderId != 0 || Portfolio.Values.Any(x => x.Symbol.Value == "EURUSD" && x.Invested);
    }

    private void RefreshAtr()
    {
        if (_m5.Count < AtrPeriod + 1) { _atr = 0m; return; }
        var trueRanges = _m5.Select((bar, i) => i == 0
            ? bar.High - bar.Low
            : Math.Max(bar.High - bar.Low,
                Math.Max(Math.Abs(bar.High - _m5[i - 1].Close), Math.Abs(bar.Low - _m5[i - 1].Close)))).ToList();
        _atr = trueRanges.Skip(trueRanges.Count - AtrPeriod).Average();
    }

    private Observation Observe(DateTime boundary, DateTime m1Source)
    {
        var visibleM5 = _m5.Where(x => x.EndTime <= boundary).ToList();
        var m1 = _m1;
        var m1Stoch = Stochastic(m1);
        var m5Stoch = Stochastic(visibleM5);
        var ema = m1.Count == 0 ? 0m : Ema(m1.Select(x => x.Close).ToList(), EmaPeriod);
        var m5Source = visibleM5.LastOrDefault()?.Time;
        var result = new Observation
        {
            Boundary = boundary, M1SourceOpen = m1Source, M5SourceOpen = m5Source,
            M1K = m1Stoch.CurrentK, M1D = m1Stoch.CurrentD, M5K = m5Stoch.CurrentK, M5D = m5Stoch.CurrentD,
            Ema = ema, Atr = _atr ?? 0m, Signal = "NONE", Reason = "INSUFFICIENT_HISTORY"
        };
        if (m1Stoch.K.Count == 0 || m5Stoch.K.Count == 0) return result;
        var current = m1.Last();
        var buy = m5Stoch.CurrentK > m5Stoch.CurrentD && m1Stoch.K.TakeLast(10).Any(x => x < 20m)
            && m1Stoch.CurrentK > m1Stoch.CurrentD;
        var sell = m5Stoch.CurrentK < m5Stoch.CurrentD && m1Stoch.K.TakeLast(10).Any(x => x > 80m)
            && m1Stoch.CurrentK < m1Stoch.CurrentD;
        result.Reason = "NO_SIGNAL";
        if (buy && current.Close > ema && current.Close > current.Open) { result.Signal = "BUY"; result.Reason = "ENTRY_CONDITIONS"; }
        else if (sell && current.Close < ema && current.Close < current.Open) { result.Signal = "SELL"; result.Reason = "ENTRY_CONDITIONS"; }
        else if (buy || sell) result.Reason = "EMA_CANDLE_FILTER";
        return result;
    }

    private static decimal Ema(IReadOnlyList<decimal> values, int period)
    {
        var alpha = 2m / (period + 1m);
        var value = values[0];
        for (var i = 1; i < values.Count; i++) value = alpha * values[i] + (1m - alpha) * value;
        return value;
    }

    private static StochasticValue Stochastic(IReadOnlyList<M031Bar> bars)
    {
        var k = new List<decimal>();
        if (bars.Count < KPeriod + DPeriod + Slowing) return new StochasticValue(k, new List<decimal>());
        for (var i = 0; i < bars.Count; i++)
        {
            if (i < KPeriod - 1) { k.Add(0m); continue; }
            var window = bars.Skip(i - KPeriod + 1).Take(KPeriod).ToList();
            var high = window.Max(x => x.High); var low = window.Min(x => x.Low);
            if (i < KPeriod - 1 + Slowing - 1) { k.Add(0m); continue; }
            decimal numerator = 0m, denominator = 0m;
            for (var j = i - Slowing + 1; j <= i; j++)
            {
                var local = bars.Skip(j - KPeriod + 1).Take(KPeriod).ToList();
                var localHigh = local.Max(x => x.High); var localLow = local.Min(x => x.Low);
                numerator += bars[j].Close - localLow; denominator += localHigh - localLow;
            }
            k.Add(denominator == 0m ? 100m : numerator / denominator * 100m);
        }
        var d = new List<decimal>();
        for (var i = 0; i < k.Count; i++) d.Add(i >= DPeriod - 1 && i >= KPeriod - 1 + Slowing - 1 ? k.Skip(i - DPeriod + 1).Take(DPeriod).Average() : 0m);
        return new StochasticValue(k, d);
    }

    private void AttachProtectionIfReady(int orderId, string side)
    {
        if (!_atr.HasValue || _atr <= 0m || !Portfolio.TryGetValue(Symbol.Create("EURUSD", SecurityType.Forex, Market.Oanda), out var holding)) return;
        var price = holding.AveragePrice;
        var sl = side == "BUY" ? price - _atr.Value : price + _atr.Value;
        var tp = side == "BUY" ? price + 2m * _atr.Value : price - 2m * _atr.Value;
        StopMarketOrder(holding.Symbol, side == "BUY" ? -holding.Quantity : -holding.Quantity, sl, "M031|SL");
        LimitOrder(holding.Symbol, side == "BUY" ? -holding.Quantity : -holding.Quantity, tp, "M031|TP");
        EmitEvent("SLTP_MODIFY", Time, Time - TimeSpan.FromMinutes(1), null, side, sl: sl, tp: tp, positionId: orderId, reason: "0_MODIFIED");
    }

    private void AppendTrace(Observation o)
    {
        var row = new { record_type = "indicator_observation", schema_version = Schema, source_engine = "lean", symbol = "EURUSD", event_kind = "OBSERVATION", utc_time_ms = new DateTimeOffset(o.Boundary).ToUnixTimeMilliseconds(), m1_source_open_utc = Iso(o.M1SourceOpen), m5_source_open_utc = o.M5SourceOpen.HasValue ? Iso(o.M5SourceOpen.Value) : null, m1_k = o.M1K, m1_d = o.M1D, m5_k = o.M5K, m5_d = o.M5D, ema = o.Ema, atr = o.Atr, candidate_signal = o.Signal, blocked_by_position = IsBlocked() };
        _trace.AppendLine(JsonConvert.SerializeObject(row));
    }

    private void EmitEvent(string kind, DateTime boundary, DateTime m1Source, DateTime? m5Source, string? side, decimal? m1K = null, decimal? m1D = null, decimal? m5K = null, decimal? m5D = null, decimal? ema = null, decimal? atr = null, decimal? entryPrice = null, decimal? sl = null, decimal? tp = null, int? requestId = null, int? positionId = null, string? reason = null)
    {
        var row = new { schema_version = Schema, source_engine = "lean", symbol = "EURUSD", event_kind = kind, utc_time_ms = new DateTimeOffset(boundary).ToUnixTimeMilliseconds(), m1_source_open_utc = Iso(m1Source), m5_source_open_utc = m5Source.HasValue ? Iso(m5Source.Value) : null, side, request_id = requestId, position_id = positionId, volume_lots = side == null ? (decimal?)null : Volume, m1_k = m1K, m1_d = m1D, m5_k = m5K, m5_d = m5D, ema, atr, entry_or_exit_price = entryPrice, sl, tp, reason_or_error_code = reason };
        _events.AppendLine(JsonConvert.SerializeObject(row));
    }

    private string BuildManifest()
    {
        var hashes = new Dictionary<string, string>();
        foreach (var pair in new[] { ("m1", M031SourcePaths.M1), ("m1_ask", M031SourcePaths.M1Ask), ("m5", M031SourcePaths.M5) })
            if (System.IO.File.Exists(pair.Item2)) using (var sha = SHA256.Create()) hashes[pair.Item1] = Convert.ToHexString(sha.ComputeHash(System.IO.File.ReadAllBytes(pair.Item2))).ToLowerInvariant();
        return JsonConvert.SerializeObject(new { schema_version = 1, source_engine = "lean", source_interval_utc = new { start = _sampleStart, end = _sampleEnd }, canonical_m5_direct = true, hashes, parameters = new { k_period = KPeriod, d_period = DPeriod, slowing = Slowing, ema_period = EmaPeriod, atr_period = AtrPeriod, volume = Volume } }, Formatting.Indented);
    }

    private void ValidateInputSeal()
    {
        var expected = new Dictionary<string, (string Path, string Hash)>
        {
            ["m1"] = (M031SourcePaths.M1, ExpectedM1Sha256),
            ["m1_ask"] = (M031SourcePaths.M1Ask, ExpectedM1AskSha256),
            ["m5"] = (M031SourcePaths.M5, ExpectedM5Sha256)
        };
        foreach (var item in expected)
        {
            if (!System.IO.File.Exists(item.Value.Path))
                throw new InvalidOperationException($"missing sealed M031 source: {item.Value.Path}");
            using var sha = SHA256.Create();
            var actual = Convert.ToHexString(sha.ComputeHash(System.IO.File.ReadAllBytes(item.Value.Path))).ToLowerInvariant();
            if (!StringComparer.Ordinal.Equals(actual, item.Value.Hash))
                throw new InvalidOperationException($"M031 source hash mismatch for {item.Key}: expected {item.Value.Hash}, got {actual}");
        }
        if (_sampleStart != new DateTime(2026, 9, 10, 0, 0, 0, DateTimeKind.Utc)
            || _sampleEnd != new DateTime(2026, 9, 11, 0, 0, 0, DateTimeKind.Utc))
            throw new InvalidOperationException("M031 sample interval is not the sealed UTC day");
    }

    private static string Iso(DateTime value) => new DateTimeOffset(value, TimeSpan.Zero).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);

    private sealed record M031Bar(DateTime Time, DateTime EndTime, decimal Open, decimal High, decimal Low, decimal Close, long Spread);
    private sealed record StochasticValue(List<decimal> K, List<decimal> D)
    {
        public decimal CurrentK => K.Count == 0 ? 0m : K[^1];
        public decimal CurrentD => D.Count == 0 ? 0m : D[^1];
    }
    private sealed class Observation
    {
        public DateTime Boundary { get; init; }
        public DateTime M1SourceOpen { get; init; }
        public DateTime? M5SourceOpen { get; init; }
        public decimal M1K { get; init; }
        public decimal M1D { get; init; }
        public decimal M5K { get; init; }
        public decimal M5D { get; init; }
        public decimal Ema { get; init; }
        public decimal Atr { get; init; }
        public string Signal { get; set; } = "NONE";
        public string Reason { get; set; } = "INSUFFICIENT_HISTORY";
    }
}
