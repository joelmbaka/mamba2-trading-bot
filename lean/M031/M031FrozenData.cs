// Independent M031 frozen-source adapters.
// This file intentionally has no dependency on the Mamba2 Python project.
#nullable enable

using System;
using System.Globalization;
using QuantConnect;
using QuantConnect.Data;

namespace Mamba2.M031;

public static class M031SourcePaths
{
    public static string M1 { get; set; } = "data/m031/EURUSD_M1.csv";
    public static string M1Ask { get; set; } = "data/m031/EURUSD_M1_ask.csv";
    public static string M5 { get; set; } = "data/m031/EURUSD_M5.csv";

    public static string For(string kind) => kind switch
    {
        "M1" => M1,
        "M1_ASK" => M1Ask,
        "M5" => M5,
        _ => throw new ArgumentOutOfRangeException(nameof(kind), kind, "unknown M031 source")
    };
}

public abstract class M031CsvBar : BaseData
{
    protected abstract string SourceKind { get; }
    protected abstract int DurationMinutes { get; }
    protected abstract M031CsvBar Create();

    public override SubscriptionDataSource GetSource(SubscriptionDataConfig config,
        DateTime date, bool isLiveMode)
    {
        if (isLiveMode) throw new NotSupportedException("M031 sealed data is backtest-only");
        return new SubscriptionDataSource(
            M031SourcePaths.For(SourceKind),
            SubscriptionTransportMedium.LocalFile,
            FileFormat.Csv);
    }

    public override BaseData Reader(SubscriptionDataConfig config, string line,
        DateTime date, bool isLiveMode)
    {
        if (string.IsNullOrWhiteSpace(line) || line.StartsWith("time", StringComparison.OrdinalIgnoreCase))
            return null!;

        var fields = line.Split(',');
        if (fields.Length < 5 || !long.TryParse(fields[0], NumberStyles.Integer,
            CultureInfo.InvariantCulture, out var unixSeconds))
            return null!;

        // LEAN may request the same full-file source for successive UTC days.
        // Emit only that day\x27s bar: otherwise daily source renewal can replay
        // earlier history and invalidate first-source EMA and event counts.
        var timestamp = DateTimeOffset.FromUnixTimeSeconds(unixSeconds).UtcDateTime;
        if (timestamp.Date != date.Date) return null!;

        var open = decimal.Parse(fields[1], CultureInfo.InvariantCulture);
        var high = decimal.Parse(fields[2], CultureInfo.InvariantCulture);
        var low = decimal.Parse(fields[3], CultureInfo.InvariantCulture);
        var close = decimal.Parse(fields[4], CultureInfo.InvariantCulture);

        var result = Create();
        result.Symbol = config.Symbol;
        result.Time = timestamp;
        result.EndTime = timestamp.AddMinutes(DurationMinutes);
        result.Open = open;
        result.High = high;
        result.Low = low;
        result.Close = close;
        result.Value = close; // Required BaseData price for LEAN custom subscriptions.
        result.TickVolume = fields.Length > 5 ? long.Parse(fields[5], CultureInfo.InvariantCulture) : 0;
        result.Spread = fields.Length > 6 ? long.Parse(fields[6], CultureInfo.InvariantCulture) : 0;
        result.RealVolume = fields.Length > 7 ? long.Parse(fields[7], CultureInfo.InvariantCulture) : 0;
        return result;
    }

    public decimal Open { get; protected set; }
    public decimal High { get; protected set; }
    public decimal Low { get; protected set; }
    public decimal Close { get; protected set; }
    public long TickVolume { get; protected set; }
    public long Spread { get; protected set; }
    public long RealVolume { get; protected set; }

}

public sealed class M031M1 : M031CsvBar
{
    protected override string SourceKind => "M1";
    protected override int DurationMinutes => 1;
    protected override M031CsvBar Create() => new M031M1();
}

public sealed class M031M1Ask : M031CsvBar
{
    protected override string SourceKind => "M1_ASK";
    protected override int DurationMinutes => 1;
    protected override M031CsvBar Create() => new M031M1Ask();
}

public sealed class M031M5 : M031CsvBar
{
    protected override string SourceKind => "M5";
    protected override int DurationMinutes => 5;
    protected override M031CsvBar Create() => new M031M5();
}
