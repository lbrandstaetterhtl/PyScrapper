using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// ViewModel for the CodecConverterWindow, responsible for handling the logic of converting media files using ffmpeg.
/// It manages the input and output file paths, conversion status, progress, and cancellation.
/// The ViewModel interacts with the ffmpeg process to perform the conversion and updates the UI accordingly.
/// It also handles errors that may occur during the conversion process and logs relevant messages using the AppLogger.
/// Upon successful conversion, it adds the converted media to the AppData and closes the window.
/// If any errors occur, it displays an error message and closes the window without adding the media to the AppData.
/// </summary>
public partial class CodecConverterWindowViewModel : ObservableObject
{
    [ObservableProperty] private string _inputFilePath = string.Empty;

    [ObservableProperty] private string _outputFilePath = string.Empty;

    [ObservableProperty] private string _statusMessage = "Ready to convert";

    [ObservableProperty] private double _progressValue = 0;

    private readonly CancellationTokenSource _cts = new();

    [ObservableProperty] private bool _started = false;

    public bool StartButtonEnabled => !Started;
    
    private readonly Window _window;
    
    private Process? _process;
    
    private readonly AppLogger _logger = AppLogger.Instance;

    /// <summary>
    /// CancelConversion method that is executed when the user clicks the cancel button during the conversion process.
    /// It cancels the ongoing conversion by signaling the cancellation token and attempts to kill the ffmpeg process if it is still running.
    /// If an error occurs while killing the process, it logs the error message and updates the status message accordingly.
    /// Finally, it closes the window without adding the media to the AppData, indicating that the conversion was not successful.
    /// </summary>
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
            var log = new Message("Error while killing process: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            StatusMessage = "Error while killing process: " + e.Message;
        }
        _window.Close(false);
    }

    /// <summary>
    /// StartConversion method that is executed when the user clicks the start button to initiate the conversion process.
    /// It starts by setting the status message and progress value, then retrieves the duration of the input media file using ffprobe.
    /// It then starts the ffmpeg process to perform the conversion, redirecting the standard output and error to capture progress and any errors that may occur.
    /// </summary>
    /// <exception cref="Exception"></exception>
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
                duration = await GetDuration(InputFilePath);
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
                    Arguments = $"-y -i \"{InputFilePath}\" -c:v libx264 -c:a aac -progress pipe:1 -nostats -loglevel error \"{OutputFilePath}\"",
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
            
            var log = new Message("Conversion completed successfully!", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var req = new CreateDownloadedMediaRequest()
            {
                UserIdentifier = AppData.CurrentUser.Identifier,
                Url = "N/A",
                DownloadPath = OutputFilePath,
                MediaType = OutputFilePath.Split('.')[^1],
                DownloadedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                IsPlayable = true,
                Title = System.IO.Path.GetFileNameWithoutExtension(OutputFilePath)
            };

            DownloadedMedia newMedia = await Database.CreateDownloadedMediaAsync(req);
            
            AppData.AddDownloadedMedia(newMedia);
            
            _window.Close(true);
        }
        catch (Exception e)
        {
            StatusMessage = "Error during conversion: " + e.Message;
            var log = new Message("Error during conversion: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            _window.Close(false);
        }
        finally
        {
            Started = false;
        }
    }
    
    
    /// <summary>
    /// GetDuration method that uses ffprobe to retrieve the duration of the input media file.
    /// </summary>
    /// <param name="filePath"></param>
    /// <returns></returns>
    /// <exception cref="Exception"></exception>
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

    /// <summary>
    /// SetOutputPath method that generates the output file path based on the input file path by appending "_converted" to the file name and changing the extension to .mp4.
    /// </summary>
    /// <param name="path"></param>
    /// <returns></returns>
    public static string SetOutputPath(string path)
    {
        return System.IO.Path.Combine(System.IO.Path.GetDirectoryName(path) ?? "",
            System.IO.Path.GetFileNameWithoutExtension(path) + "_converted.mp4");
    }
    
    /// <summary>
    /// Constructor for the CodecConverterWindowViewModel that takes a Window as a parameter and initializes the _window field with the provided window instance.
    /// </summary>
    /// <param name="window"></param>
    public CodecConverterWindowViewModel(Window window)
    {
        _window = window;
    }
}