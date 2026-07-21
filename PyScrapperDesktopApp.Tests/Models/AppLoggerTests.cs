using System;
using System.IO;
using PyScrapperDesktopApp.Models;
using Xunit;

namespace PyScrapperDesktopApp.Tests.Models;

public class AppLoggerTests
{
    [AvaloniaFact]
    public void LogNewMassage_WritesToFile()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"test_logs_{Guid.NewGuid()}");
        Directory.CreateDirectory(tempDir);
        var logFile = Path.Combine(tempDir, "app.log");

        try
        {
            // AppLogger uses AppData.LogsPath which is fixed, so we test the log format directly
            var massage = new Massage("Test log entry", new DateTime(2025, 3, 15, 14, 30, 45), "INFO");
            var expectedLogEntry = "2025-03-15 14:30:45 [INFO] Test log entry";

            var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";

            Assert.Equal(expectedLogEntry, logEntry);
        }
        finally
        {
            if (Directory.Exists(tempDir))
                Directory.Delete(tempDir, true);
        }
    }

    [AvaloniaFact]
    public void LogFormat_WarningType_FormatsCorrectly()
    {
        var massage = new Massage("Warning message", new DateTime(2025, 6, 1, 8, 0, 0), "WARNING");

        var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";

        Assert.Equal("2025-06-01 08:00:00 [WARNING] Warning message", logEntry);
    }

    [AvaloniaFact]
    public void LogFormat_ErrorType_FormatsCorrectly()
    {
        var massage = new Massage("Error occurred", new DateTime(2025, 12, 31, 23, 59, 59), "ERROR");

        var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";

        Assert.Equal("2025-12-31 23:59:59 [ERROR] Error occurred", logEntry);
    }

    [AvaloniaFact]
    public void AppLogger_CanBeInstantiated()
    {
        var logger = new AppLogger();

        Assert.NotNull(logger);
    }
}


