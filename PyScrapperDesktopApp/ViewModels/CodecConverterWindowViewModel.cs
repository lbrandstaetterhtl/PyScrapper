using System;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.ViewModels;

public partial class CodecConverterWindowViewModel : ObservableObject
{
    [ObservableProperty] private string _inputFilePath = string.Empty;

    [ObservableProperty] private string _outputFilePath = string.Empty;

    [ObservableProperty] private string _statusMessage = "Ready to convert";

    [ObservableProperty] private double _progressValue = 0;

    public readonly CancellationTokenSource _cts = new();

    [ObservableProperty] private bool _started = false;

    public bool StartButtonEnabled => !Started;
    
    private Process? _process;

    public event Action? CloseRequested;

    [RelayCommand]
    private void CancelConversion()
    {
        _cts.Cancel();
        try
        {
            _process?.Kill();
        }
        catch (Exception e)
        {
            var logger = new AppLogger();
            var log = new Massage("Error while killing process: " + e.Message, DateTime.Now, "ERROR");
            logger.LogNewMassage(log);
            StatusMessage = "Error while killing process: " + e.Message;
        }
        CloseRequested?.Invoke();
    }

    [RelayCommand]
    private async Task StartConversion()
    {
        try
        {
            var process = new Process();
            process.EnableRaisingEvents = true;

            process.StartInfo = new ProcessStartInfo()
            {
                FileName = "ffmpeg",
                Arguments =
                    $"-y -i \"{_inputFilePath}\" -c:v libx264 -c:a aac -progress pipe:1 -nostats \"{OutputFilePath}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };

            process.Start();
            
            _process = process;

            double duration = 0;

            try
            {
                duration = await GetDuration(_inputFilePath);
            }
            catch (Exception e)
            {
                var logger = new AppLogger();
                var log = new Massage("Error while getting duration: " + e.Message, DateTime.Now, "ERROR");
                logger.LogNewMassage(log);
                StatusMessage = "Error while getting duration: " + e.Message;
                return;
            }

            var errorReaderTask = Task.Run(async () =>
            {
                while (!process.StandardError.EndOfStream)
                {
                    var errLine = await process.StandardError.ReadLineAsync();
                    if (errLine != null)
                    {
                        var logger = new AppLogger();
                        var log = new Massage("FFmpeg error: " + errLine, DateTime.Now, "ERROR");
                        logger.LogNewMassage(log);

                        Dispatcher.UIThread.Post(() => { StatusMessage = "FFmpeg error: " + errLine; });

                        _cts.Cancel();
                    }
                }
            });
            
            errorReaderTask.RunSynchronously();

            while (!process.StandardOutput.EndOfStream && !_cts.Token.IsCancellationRequested)
            {
                var line = await process.StandardOutput.ReadLineAsync();
                if (line != null)
                {
                    if (line.StartsWith("out_time_ms="))
                    {
                        var outTimeMsStr = line.Substring("out_time_ms=".Length);
                        if (long.TryParse(outTimeMsStr, out var outTimeMs))
                        {
                            Dispatcher.UIThread.Post(() =>
                            {
                                ProgressValue = duration > 0 ? (outTimeMs / 1000000.0) / duration * 100 : 0;
                                StatusMessage = $"Converting... {ProgressValue:F2}%";
                            });
                        }
                    }
                }
            }

            await process.WaitForExitAsync(_cts.Token);
        }
        catch (Exception e)
        {
            var logger = new AppLogger();
            var log = new Massage("Error during conversion: " + e.Message, DateTime.Now, "ERROR");
            logger.LogNewMassage(log);
            StatusMessage = "Error during conversion: " + e.Message;
        }
    }

    private async Task<double> GetDuration(string filePath)
    {
        var process = new Process();

        process.StartInfo.FileName = "ffprobe";
        process.StartInfo.Arguments =
            $"-v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{filePath}\"";

        process.StartInfo.RedirectStandardOutput = true;
        process.StartInfo.UseShellExecute = false;
        process.StartInfo.CreateNoWindow = true;

        process.Start();

        var output = await process.StandardOutput.ReadToEndAsync();
        await process.WaitForExitAsync();

        if (double.TryParse(output, System.Globalization.NumberStyles.Any,
                System.Globalization.CultureInfo.InvariantCulture, out var duration))
        {
            return duration;
        }

        throw new Exception("Could not parse duration from ffprobe output: " + output);
    }

    public static string SetOutputPath(string path)
    {
        return System.IO.Path.Combine(System.IO.Path.GetDirectoryName(path) ?? "",
            System.IO.Path.GetFileNameWithoutExtension(path) + "_converted.mp4");
    }
}