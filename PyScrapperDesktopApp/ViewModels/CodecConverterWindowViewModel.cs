using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

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
    
    private readonly Window _window;
    
    private Process? _process;
    
    private readonly AppLogger _logger = new();

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
            var log = new Massage("Error while killing process: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            StatusMessage = "Error while killing process: " + e.Message;
        }
        _window.Close(false);
    }

    [RelayCommand]
    private async Task StartConversion()
    {
        try
        {
            Started = true;
            StatusMessage = "Starting conversion...";
            ProgressValue = 0;

            double duration;
            try
            {
                duration = await GetDuration(_inputFilePath);
            }
            catch (Exception e)
            {
                StatusMessage = "Error while getting duration: " + e.Message;
                return;
            }

            var process = new Process
            {
                EnableRaisingEvents = true,
                StartInfo = new ProcessStartInfo
                {
                    FileName = "ffmpeg",
                    Arguments = $"-y -i \"{_inputFilePath}\" -c:v libx264 -c:a aac -progress pipe:1 -nostats -loglevel error \"{OutputFilePath}\"",
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                } 
            };

            var ffmpegErrors = new List<string>();

            process.Start();
            _process = process;

            var errorReaderTask = Task.Run(async () =>
            {
                while (!process.StandardError.EndOfStream)
                {
                    var errLine = await process.StandardError.ReadLineAsync();
                    if (!string.IsNullOrWhiteSpace(errLine))
                    {
                        lock (ffmpegErrors)
                        {
                            ffmpegErrors.Add(errLine);
                        }
                    }
                }
            });

            while (!_cts.Token.IsCancellationRequested)
            {
                var line = await process.StandardOutput.ReadLineAsync();
                if (line == null)
                    break;

                if (line.StartsWith("out_time_us="))
                {
                    var value = line["out_time_us=".Length..];
                    if (long.TryParse(value, out var outTimeUs))
                    {  
                        var progress = duration > 0
                        ? (outTimeUs / 1_000_000.0) / duration * 100
                        : 0;

                        await Dispatcher.UIThread.InvokeAsync(() =>
                        {
                            ProgressValue = progress;
                            StatusMessage = $"Converting... {ProgressValue:F2}%";
                        });
                    }
                }
                else if (line.StartsWith("progress="))
                {
                    await Dispatcher.UIThread.InvokeAsync(() =>
                    {
                        StatusMessage = line == "progress=end"
                        ? "Conversion finished."
                        : "Converting...";
                    });
                }
            }

            await process.WaitForExitAsync(_cts.Token);
            await errorReaderTask;

            if (process.ExitCode != 0)
            {
                var errorText = string.Join(Environment.NewLine, ffmpegErrors);
                throw new Exception($"ffmpeg exited with code {process.ExitCode}. {errorText}");
            }

            await Dispatcher.UIThread.InvokeAsync(() =>
            {
                ProgressValue = 100;
                StatusMessage = "Conversion finished.";
            });

            var messageBox = new MessageBox("Conversion completed successfully!");
            await messageBox.ShowDialog(_window);
            
            var log = new Massage("Conversion completed successfully!", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            _window.Close(true);
        }
        catch (Exception e)
        {
            StatusMessage = "Error during conversion: " + e.Message;
            _window.Close(false);
        }
        finally
        {
            Started = false;
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
    
    public CodecConverterWindowViewModel(Window window)
    {
        _window = window;
    }
}