using System;
using System.Collections.Concurrent;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Thread-safe logger that queues messages and writes them to app.log on a single
/// background thread. This prevents "file is being used by another process" errors
/// that occur when multiple threads try to write to the same file at once.
/// </summary>
public class AppLogger : Interfaces.IAppLogger, IDisposable
{
    private static readonly Lazy<AppLogger> _instance = new(() => new AppLogger());
    public static AppLogger Instance => _instance.Value;

    private readonly ConcurrentQueue<string> _queue = new();

    private readonly SemaphoreSlim _signal = new(0);

    private readonly CancellationTokenSource _cts = new();

    private readonly Task _worker;

    private readonly string _logFilePath;
    private AppLogger()
    {
        _logFilePath = Path.Combine(AppData.AppLogsPath, "app.log");
        Directory.CreateDirectory(Path.GetDirectoryName(_logFilePath)!);

        _worker = Task.Run(ProcessQueueAsync);
    }

    /// <summary>
    /// Enqueues a message. Returns immediately — the caller does NOT wait for disk I/O.
    /// Safe to call from any thread.
    /// </summary>
    public void LogNewMassage(Message massage)
    {
        var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";
        _queue.Enqueue(logEntry);
        _signal.Release();
    }

    /// <summary>
    /// Same as LogNewMassage but also prints to the console for real-time debugging.
    /// </summary>
    public void LogDebugMessage(Message massage)
    {
        var logEntry = $"{massage.Timestamp:yyyy-MM-dd HH:mm:ss} [{massage.Type}] {massage.Text}";
        Console.WriteLine(logEntry);

        _queue.Enqueue(logEntry);
        _signal.Release();
    }

    /// <summary>
    /// The single consumer loop. Runs until shutdown. This is the ONLY code
    /// that touches the file, so there is never a write conflict.
    /// </summary>
    private async Task ProcessQueueAsync()
    {
        while (true)
        {
            try
            {
                await _signal.WaitAsync(_cts.Token);
            }
            catch (OperationCanceledException)
            {
                break; 
            }
            
            while (_queue.TryDequeue(out var entry))
            {
                try
                {
                    File.AppendAllText(_logFilePath, entry + Environment.NewLine);
                }
                catch (IOException)
                {
                    _queue.Enqueue(entry);
                    await Task.Delay(50);
                    break;
                }
                catch (Exception ex)
                {
                    
                    Console.WriteLine($"[AppLogger] Failed to write log: {ex.Message}");
                }
            }
        }
        
        while (_queue.TryDequeue(out var entry))
        {
            try { File.AppendAllText(_logFilePath, entry + Environment.NewLine); }
            catch {}
        }
    }

    /// <summary>
    /// Call this on app shutdown to flush remaining logs and stop the background thread.
    /// </summary>
    public void Dispose()
    {
        _cts.Cancel();
        _signal.Release();
        try
        {
            _worker.Wait(TimeSpan.FromSeconds(5));
        }
        catch {}

        _cts.Dispose();
        _signal.Dispose();
    }
}

/// <summary>
/// Represents a single log message with text, timestamp, and type (INFO, ERROR, etc.).
/// </summary>
public class Message(string text, DateTime timestamp, string type)
{
    public string Text => text;
    public DateTime Timestamp => timestamp;
    public string Type => type;
}