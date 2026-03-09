using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class MediaPlayerWindowViewModelTests
{
    [Fact]
    public void FormatTime_ZeroSeconds_ReturnsZeroZero()
    {
        // FormatTime is private static, test via reflection
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        Assert.NotNull(method);

        var result = (string)method.Invoke(null, new object[] { 0L })!;
        Assert.Equal("0:00", result);
    }

    [Fact]
    public void FormatTime_60Seconds_Returns1Minute()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { 60L })!;
        Assert.Equal("1:00", result);
    }

    [Fact]
    public void FormatTime_90Seconds_Returns1Minute30()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { 90L })!;
        Assert.Equal("1:30", result);
    }

    [Fact]
    public void FormatTime_3661Seconds_Returns1Hour1Minute1Second()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { 3661L })!;
        Assert.Equal("1:01:01", result);
    }

    [Fact]
    public void FormatTime_NegativeSeconds_TreatedAsZero()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { -10L })!;
        Assert.Equal("0:00", result);
    }

    [Fact]
    public void FormatTime_59Seconds_Returns0MinuteAnd59Seconds()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { 59L })!;
        Assert.Equal("0:59", result);
    }

    [Fact]
    public void FormatTime_3600Seconds_Returns1Hour()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { 3600L })!;
        Assert.Equal("1:00:00", result);
    }

    [Fact]
    public void FormatTime_LargeValue_FormatsCorrectly()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        // 2 hours, 30 minutes, 15 seconds = 9015 seconds
        var result = (string)method!.Invoke(null, new object[] { 9015L })!;
        Assert.Equal("2:30:15", result);
    }

    [Fact]
    public void FormatTime_5Seconds_Returns0Colon05()
    {
        var method = typeof(MediaPlayerWindowViewModel)
            .GetMethod("FormatTime", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);

        var result = (string)method!.Invoke(null, new object[] { 5L })!;
        Assert.Equal("0:05", result);
    }
}

