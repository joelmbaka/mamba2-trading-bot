// M031 independent, observation-only LEAN candidate-signal comparison.
// This intentionally sends NO orders. It cannot assert broker/fill parity.
// Separate C# calculations; no Mamba2 Python strategy or indicator imports.
#nullable enable

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Data;

namespace Mamba2.M031;

public sealed class M031FrozenBaselineAlgorithm : QCAlgorithm
{
    private const string Schema = "m030.events.v1";
    private const string ExpectedM1Sha256 = "19a3a92141989e9d1ed174447e43ada627c13ed8b3cef39d800a07d587fdc2fe";
    private const string ExpectedM1AskSha256 = "7cca2326ead010df7dcc38fdbd787ec051804ce7145b4645325ea9f67ca0548c";
    private const string ExpectedM5Sha256 = "c8dc043c301531b11452a95273bd2fceec8f7ca933d99c5d7338d3f4ab2bb2e9";
    private static readonly DateTime SealedStart = new(2026, 9, 10, 0, 0, 0, DateTimeKind.Utc);
    private static readonly DateTime SealedEnd = new(2026, 9, 11, 0, 0, 0, DateTimeKind.Utc);

    private readonly StochasticState _m1Stochastic = new();
    private readonly StochasticState _m5Stochastic = new();
    private readonly AtrState _m5Atr = new();
    private readonly StringBuilder _trace = new();
    private readonly StringBuilder _events = new();
    private readonly Dictionary<string, string> _sourceHashes = new();
    private Symbol _m1Symbol = null!;
    private Symbol _m5Symbol = null!;
    private Symbol _askSymbol = null!;
    private string _outputPrefix = "";
    private DateTime _lastAskOpen = DateTime.MinValue;
    private DateTime _lastM1Open = DateTime.MinValue;
    private DateTime _lastM5Open = DateTime.MinValue;
    private DateTime _firstBoundary = DateTime.MinValue;
    private DateTime _lastBoundary = DateTime.MinValue;
    private decimal _ema;
    private bool _emaSeeded;
    private int _sampleM1Count;
    private int _sampleM5Count;
    private int _sampleAskCount;
    private int _candidateBuyCount;
    private int _candidateSellCount;
    private int _boundaryCount;

    public override void Initialize()
    {
        SetTimeZone(TimeZones.Utc);
        SetStartDate(2025, 8, 25);
        // Include the bar opening Sep 10 23:59, which is available Sep 11 00:00.
        SetEndDate(2026, 9, 11);
        SetCash(10000m); // No orders are permitted.

        M031SourcePaths.M1 = RequiredParameter("m1_path");
        M031SourcePaths.M1Ask = RequiredParameter("m1_ask_path");
        M031SourcePaths.M5 = RequiredParameter("m5_path");
        var start = ParseUtc(RequiredParameter("sample_start"));
        var end = ParseUtc(RequiredParameter("sample_end"));
        if (start != SealedStart || end != SealedEnd)
            throw new InvalidOperationException("M031 can only read the sealed September 10 UTC source day");

        _outputPrefix = RequiredParameter("output_prefix");
        if (!Regex.IsMatch(_outputPrefix, @"^m031/[A-Za-z0-9_-]+$"))
            throw new InvalidOperationException("output_prefix must be a unique m031/<run-id> key");
        foreach (var leaf in new[] { "input_manifest.json", "indicator_trace.jsonl", "events.jsonl", "summary.json" })
            if (ObjectStore.ContainsKey(_outputPrefix + "/" + leaf))
                throw new InvalidOperationException("refusing to overwrite existing M031 evidence: " + leaf);

        ValidateSource("m1", M031SourcePaths.M1, ExpectedM1Sha256);
        ValidateSource("m1_ask", M031SourcePaths.M1Ask, ExpectedM1AskSha256);
        ValidateSource("m5", M031SourcePaths.M5, ExpectedM5Sha256);

        // The third argument pins the data time zone; LEAN's default custom
        // data zone is US Eastern and must not leak into our UTC comparison.
        _m1Symbol = AddData<M031M1>("M031_EURUSD_M1", Resolution.Minute, TimeZones.Utc, false).Symbol;
        _askSymbol = AddData<M031M1Ask>("M031_EURUSD_M1_ASK", Resolution.Minute, TimeZones.Utc, false).Symbol;
        _m5Symbol = AddData<M031M5>("M031_EURUSD_M5", Resolution.Minute, TimeZones.Utc, false).Symbol;
    }

    public override void OnData(Slice slice)
    {
        if (slice.ContainsKey(_m5Symbol) && slice[_m5Symbol] is M031M5 m5)
        {
            var time = Utc(m5.Time);
            if (time <= _lastM5Open) throw new InvalidOperationException("M5 source is not strictly increasing");
            _lastM5Open = time;
            _m5Stochastic.Add(new Bar(time, Utc(m5.EndTime), m5.Open, m5.High, m5.Low, m5.Close));
            _m5Atr.Add(m5.High, m5.Low, m5.Close);
            if (time >= SealedStart && time < SealedEnd) _sampleM5Count++;
        }

        if (slice.ContainsKey(_askSymbol) && slice[_askSymbol] is M031M1Ask ask)
        {
            var time = Utc(ask.Time);
            if (time <= _lastAskOpen) throw new InvalidOperationException("Ask source is not strictly increasing");
            _lastAskOpen = time;
            if (time >= SealedStart && time < SealedEnd) _sampleAskCount++;
        }

        if (!slice.ContainsKey(_m1Symbol) || slice[_m1Symbol] is not M031M1 m1) return;
        var sourceOpen = Utc(m1.Time);
        var boundary = Utc(m1.EndTime);
        if (sourceOpen <= _lastM1Open) throw new InvalidOperationException("M1 source is not strictly increasing");
        if (boundary != sourceOpen.AddMinutes(1)) throw new InvalidOperationException("non-M1 source duration");
        _lastM1Open = sourceOpen;
        if (boundary > SealedEnd) return;

        _m1Stochastic.Add(new Bar(sourceOpen, boundary, m1.Open, m1.High, m1.Low, m1.Close));
        _ema = _emaSeeded ? 0.25m * m1.Close + 0.75m * _ema : m1.Close;
        _emaSeeded = true;

        // No pre-start strategy evaluation or event emission. All pre-start
        // candles are used ONLY for first-source indicator initialization.
        if (boundary <= SealedStart) return;
        if (sourceOpen < SealedStart || sourceOpen >= SealedEnd)
            throw new InvalidOperationException("sample source-open interval was exceeded");
        if (_lastAskOpen != sourceOpen)
            throw new InvalidOperationException("canonical Ask minute missing at boundary " + Iso(boundary));
        if (_lastBoundary != DateTime.MinValue && boundary != _lastBoundary.AddMinutes(1))
            throw new InvalidOperationException("missing or noncontiguous sample decision boundary");

        _firstBoundary = _boundaryCount == 0 ? boundary : _firstBoundary;
        _lastBoundary = boundary;
        _boundaryCount++;
        _sampleM1Count++;

        var observation = Observe(m1, boundary);
        EmitM1Close(boundary, sourceOpen);
        AppendCandidate(observation);
        if (observation.Signal == "BUY") _candidateBuyCount++;
        if (observation.Signal == "SELL") _candidateSellCount++;
    }

    public override void OnEndOfAlgorithm()
    {
        // A short run must NOT masquerade as matching the sealed reference.
        if (_boundaryCount != 1440 || _sampleM1Count != 1440 || _sampleAskCount != 1440 ||
            _sampleM5Count != 288 || _firstBoundary != SealedStart.AddMinutes(1) ||
            _lastBoundary != SealedEnd)
            throw new InvalidOperationException(
                $"M031 incomplete sealed day: decisions={_boundaryCount}, M1={_sampleM1Count}, " +
                $"Ask={_sampleAskCount}, M5={_sampleM5Count}, first={_firstBoundary:o}, last={_lastBoundary:o}");

        var manifest = new
        {
            schema_version = 1, executed = true, source_engine = "lean",
            mode = "independent_candidate_signal_parity_only",
            source_interval_utc = new { start = Iso(SealedStart), end = Iso(SealedEnd) },
            decision_boundaries = new { first = Iso(_firstBoundary), last = Iso(_lastBoundary), count = _boundaryCount },
            canonical_m5_direct = true, hashes = _sourceHashes,
            warmup = "first-source indicator history; no pre-sample trades",
            parameters = new { stochastic = "21/7/7", ema_period = 7, atr_period = 14 },
            execution_events_produced = false
        };
        var summary = new
        {
            schema_version = 1, decision_boundaries = _boundaryCount,
            indicator_observations = _boundaryCount,
            candidate_buy = _candidateBuyCount, candidate_sell = _candidateSellCount,
            actual_signals = 0, actual_submits = 0, actual_fills = 0,
            execution_comparison_ready = false,
            reason = "phase one compares raw candidate/indicator traces only; LEAN orders were intentionally disabled"
        };

        SaveExclusive("input_manifest.json", JsonConvert.SerializeObject(manifest, Formatting.Indented));
        SaveExclusive("indicator_trace.jsonl", _trace.ToString());
        SaveExclusive("events.jsonl", _events.ToString());
        SaveExclusive("summary.json", JsonConvert.SerializeObject(summary, Formatting.Indented));
    }

    private Observation Observe(M031M1 m1, DateTime boundary)
    {
        var result = new Observation
        {
            Boundary = boundary, M1Source = Utc(m1.Time),
            M5Source = _m5Stochastic.LastSourceTime,
            M1K = _m1Stochastic.Ready ? _m1Stochastic.K : null,
            M1D = _m1Stochastic.Ready ? _m1Stochastic.D : null,
            M5K = _m5Stochastic.Ready ? _m5Stochastic.K : null,
            M5D = _m5Stochastic.Ready ? _m5Stochastic.D : null,
            Ema = _emaSeeded ? _ema : null,
            Atr = _m5Atr.Value,
            Signal = "NONE", Reason = "INSUFFICIENT_HISTORY"
        };
        if (!_m1Stochastic.Ready || !_m5Stochastic.Ready) return result;
        var buy = _m5Stochastic.K > _m5Stochastic.D &&
            _m1Stochastic.RecentK.Any(k => k < 20m) && _m1Stochastic.K > _m1Stochastic.D;
        var sell = _m5Stochastic.K < _m5Stochastic.D &&
            _m1Stochastic.RecentK.Any(k => k > 80m) && _m1Stochastic.K < _m1Stochastic.D;
        result.Reason = "NO_SIGNAL";
        if (buy && m1.Close > _ema && m1.Close > m1.Open)
        { result.Signal = "BUY"; result.Reason = "ENTRY_CONDITIONS"; }
        else if (sell && m1.Close < _ema && m1.Close < m1.Open)
        { result.Signal = "SELL"; result.Reason = "ENTRY_CONDITIONS"; }
        else if (buy || sell)
            result.Reason = "EMA_CANDLE_FILTER";
        return result;
    }

    private void AppendCandidate(Observation value)
    {
        // 'blocked_by_position' / actual SIGNAL are intentionally not guessed.
        // Compare only Python indicator_trace.candidate_signal + indicator values.
        var row = new
        {
            record_type = "indicator_observation", schema_version = Schema,
            source_engine = "lean", symbol = "EURUSD",
            utc_time_ms = Millis(value.Boundary),
            m1_source_open_utc = Iso(value.M1Source),
            m5_source_open_utc = value.M5Source.HasValue ? Iso(value.M5Source.Value) : null,
            m1_k = value.M1K, m1_d = value.M1D,
            m5_k = value.M5K, m5_d = value.M5D,
            ema = value.Ema, atr = value.Atr,
            candidate_signal = value.Signal, reason_or_error_code = value.Reason,
            comparison_scope = "unblocked_raw_candidate_only",
            blocked_by_position = (bool?)null
        };
        _trace.AppendLine(JsonConvert.SerializeObject(row));
    }

    private void EmitM1Close(DateTime boundary, DateTime sourceOpen)
    {
        _events.AppendLine(JsonConvert.SerializeObject(new
        {
            schema_version = Schema, source_engine = "lean", symbol = "EURUSD",
            event_kind = "M1_CLOSE", utc_time_ms = Millis(boundary),
            m1_source_open_utc = Iso(sourceOpen)
        }));
    }

    private string RequiredParameter(string name)
    {
        var value = GetParameter(name);
        if (string.IsNullOrWhiteSpace(value))
            throw new InvalidOperationException("M031 required LEAN parameter is missing: " + name);
        return value;
    }

    private static DateTime ParseUtc(string value)
    {
        if (!value.EndsWith("Z", StringComparison.Ordinal))
            throw new InvalidOperationException("M031 timestamps must explicitly end in Z");
        return DateTime.Parse(value, CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
    }

    private void ValidateSource(string key, string path, string expected)
    {
        if (!File.Exists(path)) throw new InvalidOperationException("missing sealed M031 source " + key);
        using var sha = SHA256.Create();
        using var stream = File.OpenRead(path);
        var actual = Convert.ToHexString(sha.ComputeHash(stream)).ToLowerInvariant();
        if (actual != expected)
            throw new InvalidOperationException($"M031 {key} SHA-256 mismatch; expected={expected}; got={actual}");
        _sourceHashes[key] = actual;
    }

    private void SaveExclusive(string leaf, string body)
    {
        var key = _outputPrefix + "/" + leaf;
        if (ObjectStore.ContainsKey(key)) throw new InvalidOperationException("refusing to overwrite " + key);
        ObjectStore.Save(key, body);
    }

    private static DateTime Utc(DateTime value) => DateTime.SpecifyKind(value, DateTimeKind.Utc);
    private static string Iso(DateTime value) =>
        Utc(value).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture);
    private static long Millis(DateTime value) => new DateTimeOffset(Utc(value)).ToUnixTimeMilliseconds();

    private sealed record Bar(DateTime Time, DateTime EndTime,
        decimal Open, decimal High, decimal Low, decimal Close);

    private sealed class Observation
    {
        public DateTime Boundary { get; init; }
        public DateTime M1Source { get; init; }
        public DateTime? M5Source { get; init; }
        public decimal? M1K { get; init; }
        public decimal? M1D { get; init; }
        public decimal? M5K { get; init; }
        public decimal? M5D { get; init; }
        public decimal? Ema { get; init; }
        public decimal? Atr { get; init; }
        public string Signal { get; set; } = "NONE";
        public string Reason { get; set; } = "INSUFFICIENT_HISTORY";
    }

    private sealed class StochasticState
    {
        private readonly List<Bar> _bars = new();
        private readonly List<decimal> _kHistory = new();
        public DateTime? LastSourceTime => _bars.Count == 0 ? null : _bars[^1].Time;
        public bool Ready => _bars.Count >= 21 + 7 + 7;
        public decimal K => _kHistory.Count == 0 ? 0m : _kHistory[^1];
        public decimal D { get; private set; }
        public IEnumerable<decimal> RecentK => _kHistory.TakeLast(10);

        public void Add(Bar bar)
        {
            _bars.Add(bar);
            var i = _bars.Count - 1;
            decimal currentK = 0m;
            if (i >= 21 - 1 + 7 - 1)
            {
                decimal numerator = 0m, denominator = 0m;
                for (var j = i - 7 + 1; j <= i; j++)
                {
                    var highest = decimal.MinValue;
                    var lowest = decimal.MaxValue;
                    for (var index = j - 21 + 1; index <= j; index++)
                    {
                        if (_bars[index].High > highest) highest = _bars[index].High;
                        if (_bars[index].Low < lowest) lowest = _bars[index].Low;
                    }
                    numerator += _bars[j].Close - lowest;
                    denominator += highest - lowest;
                }
                currentK = denominator == 0m ? 100m : 100m * numerator / denominator;
            }
            _kHistory.Add(currentK);
            if (i >= 21 - 1 + 7 - 1 && i >= 7 - 1)
            {
                decimal sum = 0m;
                for (var n = i - 7 + 1; n <= i; n++) sum += _kHistory[n];
                D = sum / 7m;
            }
        }
    }

    private sealed class AtrState
    {
        private readonly List<decimal> _tr = new();
        private decimal? _previousClose;
        public decimal Value { get; private set; }

        public void Add(decimal high, decimal low, decimal close)
        {
            var tr = high - low;
            if (_previousClose.HasValue)
            {
                tr = Math.Max(tr, Math.Max(Math.Abs(high - _previousClose.Value),
                    Math.Abs(low - _previousClose.Value)));
            }
            _tr.Add(tr);
            _previousClose = close;
            if (_tr.Count < 15) { Value = 0m; return; }
            decimal total = 0m;
            for (var i = _tr.Count - 14; i < _tr.Count; i++) total += _tr[i];
            Value = total / 14m;
        }
    }
}
