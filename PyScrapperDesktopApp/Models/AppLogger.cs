using System;
using System.IO;
using Tmds.DBus.Protocol;

namespace PyScrapperDesktopApp.Models;

public class AppLogger
{
    public void LogNewMassage(Massage massage)
    {
        var exeDir = AppContext.BaseDirectory;
        var repoRoot = Directory.GetParent(exeDir)!.Parent!.Parent!.Parent!.FullName;
        
        var logFilePath = Path.Combine(repoRoot, @"logs\app.log");
        
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
}

public class Massage (string text, DateTime timestamp, string type)
{
    public string Text => text;
    public DateTime Timestamp => timestamp;
    public string Type => type;
}