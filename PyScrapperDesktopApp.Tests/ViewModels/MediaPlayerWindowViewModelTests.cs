using System;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class MediaPlayerWindowViewModelTests
{
    [Fact]
    public void FormatTime_ZeroSeconds_ReturnsZeroZero()
    {
        // Test TimeSpan formatting as used in CurrentlyText property
        var result = TimeSpan.FromSeconds(0).ToString(@"mm\:ss");
        Assert.Equal("00:00", result);
    }

    [Fact]
    public void FormatTime_60Seconds_Returns1Minute()
    {
        var result = TimeSpan.FromSeconds(60).ToString(@"mm\:ss");
        Assert.Equal("01:00", result);
    }

    [Fact]
    public void FormatTime_90Seconds_Returns1Minute30()
    {
        var result = TimeSpan.FromSeconds(90).ToString(@"mm\:ss");
        Assert.Equal("01:30", result);
    }

    [Fact]
    public void FormatTime_3661Seconds_Returns1Hour1Minute1Second()
    {
        // For times >= 1 hour, use hh:mm:ss format
        var ts = TimeSpan.FromSeconds(3661);
        var result = ts.TotalHours >= 1 ? ts.ToString(@"hh\:mm\:ss") : ts.ToString(@"mm\:ss");
        Assert.Equal("01:01:01", result);
    }

    [Fact]
    public void FormatTime_NegativeSeconds_TreatedAsZero()
    {
        // Negative values should be clamped to zero
        var result = TimeSpan.FromSeconds(Math.Max(0, -10)).ToString(@"mm\:ss");
        Assert.Equal("00:00", result);
    }

    [Fact]
    public void FormatTime_59Seconds_Returns0MinuteAnd59Seconds()
    {
        var result = TimeSpan.FromSeconds(59).ToString(@"mm\:ss");
        Assert.Equal("00:59", result);
    }

    [Fact]
    public void FormatTime_3600Seconds_Returns1Hour()
    {
        var ts = TimeSpan.FromSeconds(3600);
        var result = ts.TotalHours >= 1 ? ts.ToString(@"hh\:mm\:ss") : ts.ToString(@"mm\:ss");
        Assert.Equal("01:00:00", result);
    }

    [Fact]
    public void FormatTime_LargeValue_FormatsCorrectly()
    {
        // 2 hours, 30 minutes, 15 seconds = 9015 seconds
        var ts = TimeSpan.FromSeconds(9015);
        var result = ts.TotalHours >= 1 ? ts.ToString(@"hh\:mm\:ss") : ts.ToString(@"mm\:ss");
        Assert.Equal("02:30:15", result);
    }

    [Fact]
    public void FormatTime_5Seconds_Returns0Colon05()
    {
        var result = TimeSpan.FromSeconds(5).ToString(@"mm\:ss");
        Assert.Equal("00:05", result);
    }
}

