using System;
using System.IO;
using Tmds.DBus.Protocol;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Logger class responsible for logging messages to a file in the application's logs directory.
/// It ensures that the logs directory exists before writing log entries, and formats log entries with a timestamp, message type, and message text.
/// </summary>
public class AppLogger
{
    /// <summary>
    /// Logs a new message to the app.log file in the application's logs directory. If the logs directory does not exist, it creates it before writing the log entry.
    /// Each log entry is formatted with a timestamp, message type, and message text.
    /// </summary>
    /// <param name="massage"></param>
    public void LogNewMassage(Massage massage)
    {
        var logFilePath = Path.Combine(AppData.AppLogsPath, @"app.log");
        
        if (Directory.Exists(Path.GetDirectoryName(logFilePath)))
        {
            var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";
            File.AppendAllText(logFilePath, logEntry + Environment.NewLine);
        }
        else
        {
            Directory.CreateDirectory(Path.GetDirectoryName(logFilePath));
            var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";
            File.AppendAllText(logFilePath, logEntry + Environment.NewLine);
        }
    }

    public void LogDebugMessage(Massage massage)
    {
        var logger = new AppLogger();
        var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";
        Console.WriteLine(logEntry);
        
        logger.LogNewMassage(massage);
    }
}

/// <summary>
/// Class representing a log message, with properties for the message text, timestamp, and message type (e.g., INFO, ERROR, etc.).
/// </summary>
/// <param name="text"></param>
/// <param name="timestamp"></param>
/// <param name="type"></param>
public class Massage (string text, DateTime timestamp, string type)
{
    public string Text => text;
    public DateTime Timestamp => timestamp;
    public string Type => type;
}