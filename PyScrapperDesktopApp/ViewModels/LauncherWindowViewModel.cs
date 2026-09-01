using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Threading;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// Class responsible for managing the state and logic of the LauncherWindow, which serves as the automatic
/// startup window of the application. It handles checking the Python environment, installing dependencies
/// (Visual C++ Redistributable, ffmpeg, backend packages, Playwright browsers, .NET packages), starting
/// the Python backend server, and verifying that the server is responsive. Once all steps have completed
/// successfully, the window closes itself with a Success result. If an error occurs at any point, the error
/// is logged and displayed in the UI, and a Close button becomes visible for the user to dismiss the window.
/// </summary>
public partial class LauncherWindowViewModel : ObservableObject
{
    private Window _window;
    private Process _serverProcess;
    private readonly AppLogger _logger = AppLogger.Instance;

    private string RepoRoot     => AppData.PyScrapperPath;
    private string LocalServer  => Path.Combine(RepoRoot, "LocalServer");
    private string VenvPython => OperatingSystem.IsWindows()
        ? Path.Combine(LocalServer, ".venv", "Scripts", "python.exe")
        : Path.Combine(LocalServer, ".venv", "bin", "python");
    private string Requirements => Path.Combine(LocalServer, "requirements.txt");

    [ObservableProperty] 
    private ObservableCollection<LauncherMessage> _messages = new();

    [ObservableProperty]
    private bool _isLoading = true;

    [ObservableProperty]
    private bool _hasError = false;
    
    private string _installerUrl  = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe";
    private string _installerPath = Path.Combine(Path.GetTempPath(), "python-3.12.10-installer.exe");
    private DialogService _dialogService;

    /// <summary>
    /// Constructor for the LauncherWindowViewModel. Checks for design mode to avoid executing runtime code in the designer.
    /// </summary>
    public LauncherWindowViewModel(DialogService dialogService)
    {
        if (Design.IsDesignMode) return;
        
        _dialogService = dialogService;
    }

    /// <summary>
    /// Method that is called when the launcher window is ready, which sets the window reference and starts
    /// the automatic launch sequence. The sequence checks if the server is already running, then always
    /// verifies the full environment (Visual C++ Redistributable, ffmpeg, Python installation and version,
    /// pip, virtual environment, requirements, Playwright browsers) regardless of whether components already
    /// exist, restores .NET packages, starts the server, waits for a successful health check, and then
    /// closes the window with a Success result. If any step fails, the error is logged and displayed in
    /// the UI with a Close button.
    /// </summary>
    /// <param name="window"></param>
    public async void OnWindowReady(Window window)
    {
        _window = window;

        try
        {
            await Dispatcher.UIThread.InvokeAsync(() =>
            {
                Messages.Add(new LauncherMessage()
                {
                    Message = "Checking if server is running",
                    Title = "Server",
                    Symbol = "✓"
                });
            });

            var log = new Message("Checking if server is already running...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (await IsServerRunning())
            {
                log = new Message("Server is running", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
                
                await EnsureVcRedist();
                
                await RestoreDotnetPackages();
                
                await EnsureFfmpeg();
                
                await FinishSuccess();
            }
            else
            {
                throw new Exception($"Server is not running. Retry in a few minutes or contact your admin.");
            }
        }
        catch (Exception ex)
        {
            var log = new Message($"Launcher error: {ex.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            await ShowError(ex.Message);
        }
    }

    /// <summary>
    /// Method that is called when the launch sequence has completed successfully.
    /// It sets the status text to "Ready!", hides the progress bar, sets the launcher result to Success,
    /// briefly pauses so the user can see the final status, and then closes the window.
    /// </summary>
    private async Task FinishSuccess()
    {
        await Dispatcher.UIThread.InvokeAsync(() =>
        {
            Messages.Add(new LauncherMessage()
            {
                Message = "finished",
                Title = "Successfully",
                Symbol = "✓"
            });
        });

        IsLoading = false;

        if (_window is LauncherWindow launcher)
            launcher.Result = LauncherResult.Success;

        await Task.Delay(600);

        Dispatcher.UIThread.Post(() => _window.Close());
    }

    /// <summary>
    /// Method that is called when an error occurs during the launch sequence.
    /// It hides the progress bar, shows the error panel with the error message, sets the status text
    /// to "Launch failed", and sets the launcher result to Error so that App.axaml.cs can shut down
    /// the application when the window is closed.
    /// </summary>
    /// <param name="message"></param>
    private async Task ShowError(string message)
    {
        IsLoading = false;
        HasError = true;

        await Dispatcher.UIThread.InvokeAsync(() =>
        {
            Messages.Add(new LauncherMessage()
            {
                Message = message,
                Title = "Error: ",
                Symbol = "✗"
            });
        });

        if (_window is LauncherWindow launcher)
            launcher.Result = LauncherResult.Error;
    }

    /// <summary>
    /// Command method that is executed when the user clicks the Close button, which is only visible when an error
    /// has occurred. It cleans up the server process if it was started, and then closes the window.
    /// This allows the user to dismiss the launcher after reviewing the error message.
    /// </summary>
    [RelayCommand]
    private void CloseWindow()
    {
        try { _serverProcess?.Kill(entireProcessTree: true); } catch { }
        _serverProcess?.Dispose();
        _serverProcess = null;

        _window?.Close();
    }

    /// <summary>
    /// Checks if the server is already running on port 8765 by sending a GET request to the docs endpoint.
    /// Returns true if the server responds with a success status code, false otherwise.
    /// This is used to skip the startup sequence if the server was already started from a previous session.
    /// </summary>
    /// <returns></returns>
    private async Task<bool> IsServerRunning()
    {
        try
        {
            var client = new ApiClient();
            var response = await client.GetHealth();

            return response.Ok;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Restores all .NET packages by finding all .csproj files in the repository root and running
    /// dotnet restore on each one. Files in bin and obj directories are excluded from the search.
    /// The status text is updated for each project to show which one is currently being restored.
    /// </summary>
    /// <returns></returns>
    private async Task RestoreDotnetPackages()
    {
        var csprojFiles = Directory
            .GetFiles(RepoRoot, "*.csproj", SearchOption.AllDirectories)
            .Where(f => !f.Contains(Path.DirectorySeparatorChar + "bin" + Path.DirectorySeparatorChar)
                     && !f.Contains(Path.DirectorySeparatorChar + "obj" + Path.DirectorySeparatorChar))
            .ToList();

        if (csprojFiles.Count == 0) return;

        foreach (var proj in csprojFiles)
        {
            await Dispatcher.UIThread.InvokeAsync(() =>
            {
                Messages.Add(new LauncherMessage()
                {
                    Message = Path.GetFileName(proj),
                    Title = "Restoring",
                    Symbol = "✓"
                });
            });
            await RunProcess("dotnet", $"restore \"{proj}\"", RepoRoot);
        }
    }

    /// <summary>
    /// Checks if the Microsoft Visual C++ 2015-2022 Redistributable (x64) is installed by looking for
    /// VCRUNTIME140.dll in the System32 directory. If it is not found, downloads the installer from
    /// Microsoft and runs it silently. This is required for Python C-extensions such as greenlet and
    /// playwright to load correctly on Windows. On non-Windows platforms this check is skipped entirely.
    /// </summary>
    private async Task EnsureVcRedist()
    {
        if (!OperatingSystem.IsWindows()) return;

        var dll = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "VCRUNTIME140.dll");

        if (File.Exists(dll))
        {
            await Dispatcher.UIThread.InvokeAsync(() =>
            {
                Messages.Add(new LauncherMessage()
                {
                    Message = "found Visual C++ Redistributable...",
                    Title = "VcRedist Check",
                    Symbol = "✓"
                });
            });

            var log = new Message("VCRUNTIME140.dll found, skipping Visual C++ Redistributable install", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            return;
        }

        var warnLog = new Message("VCRUNTIME140.dll not found, downloading Visual C++ Redistributable...", DateTime.Now, "WARN");
        _logger.LogNewMassage(warnLog);

        Dispatcher.UIThread.Post(() => Messages.Add(new LauncherMessage()
        {
            Message = "Downloading Visual C++ Redistributable...",
            Title = "VcRdedist Check",
            Symbol = "✓"
        }));

        var installer = Path.Combine(Path.GetTempPath(), "vc_redist.x64.exe");

        using var http = new System.Net.WebClient();
        http.DownloadFile("https://aka.ms/vs/17/release/vc_redist.x64.exe", installer);

        Dispatcher.UIThread.Post(() => Messages.Add(new LauncherMessage()
        {
            Message = "installing Visual C++ Redistributable...",
            Title = "VcRedist Check",
            Symbol = "✓"
        }));

        var p = Process.Start(new ProcessStartInfo
        {
            FileName        = installer,
            Arguments       = "/install /quiet /norestart",
            UseShellExecute = true,
        })!;
        p.WaitForExit();

        try { File.Delete(installer); } catch { }

        if (!File.Exists(dll))
            throw new Exception(
                "Visual C++ Redistributable could not be installed automatically.\n" +
                "Please install it manually: https://aka.ms/vs/17/release/vc_redist.x64.exe\n" +
                "Note: installation may require administrator privileges."
            );

        var doneLog = new Message("Visual C++ Redistributable installed successfully", DateTime.Now, "INFO");
        _logger.LogNewMassage(doneLog);
    }

    /// <summary>
    /// Checks if ffmpeg is available either on PATH or in the WinGet yt-dlp.FFmpeg package directory,
    /// matching the same lookup logic used by the Python find_ffmpeg() function. If ffmpeg is not found,
    /// installs it silently via WinGet using the yt-dlp.FFmpeg package, which requires no admin privileges
    /// and places ffmpeg in the LocalAppData WinGet packages directory where find_ffmpeg() will locate it.
    /// On non-Windows platforms this check is skipped entirely.
    /// </summary>
    private async Task EnsureFfmpeg()
    {
        if (!OperatingSystem.IsWindows()) return;

        if (IsFfmpegAvailable())
        {
            await Dispatcher.UIThread.InvokeAsync(() =>
            {
                Messages.Add(new LauncherMessage()
                {
                    Message = "found Ffmpeg...",
                    Title = "Ffmpeg Check",
                    Symbol = "✓"
                });
            });

            var log = new Message("ffmpeg found, skipping install", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            return;
        }

        var warnLog = new Message("ffmpeg not found, installing via WinGet (yt-dlp.FFmpeg)...", DateTime.Now, "WARN");
        _logger.LogNewMassage(warnLog);

        Dispatcher.UIThread.Post(() => Messages.Add(new LauncherMessage()
        {
            Message = "installing Ffmpeg...",
            Title = "Ffmpeg Check",
            Symbol = "✓"
        }));

        var p = Process.Start(new ProcessStartInfo
        {
            FileName               = "winget",
            Arguments              = "install yt-dlp.FFmpeg",
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        })!;
        p.WaitForExit();

        if (!IsFfmpegAvailable())
            throw new Exception(
                "ffmpeg could not be installed automatically via WinGet.\n" +
                "Please install it manually: winget install yt-dlp.FFmpeg"
            );

        var doneLog = new Message("ffmpeg installed successfully via WinGet", DateTime.Now, "INFO");
        _logger.LogNewMassage(doneLog);
    }

    /// <summary>
    /// Checks if ffmpeg is available by first looking on PATH via the where command, then searching
    /// the WinGet packages directory for the yt-dlp.FFmpeg package. This mirrors the lookup logic of the
    /// Python find_ffmpeg() function so that both the launcher check and the Python code agree on availability.
    /// </summary>
    /// <returns></returns>
    private static bool IsFfmpegAvailable()
    {
        var where = Process.Start(new ProcessStartInfo
        {
            FileName               = "where",
            Arguments              = "ffmpeg",
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        })!;
        where.WaitForExit();
        if (where.ExitCode == 0) return true;

        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var pkgRoot = Path.Combine(localAppData, "Microsoft", "WinGet", "Packages");

        if (!Directory.Exists(pkgRoot)) return false;

        return Directory
            .EnumerateFiles(pkgRoot, "ffmpeg.exe", SearchOption.AllDirectories)
            .Any(f => f.Contains("yt-dlp.FFmpeg"));
    }
    
    /// <summary>
    /// Lädt die PATH-Umgebungsvariable für den AKTUELLEN Prozess neu.
    /// Notwendig nachdem ein Installer den PATH geändert hat, weil unser
    /// Launcher-Prozess die alte (gecachte) Version im Speicher hat.
    /// </summary>
    private static void RefreshEnvironmentPath()
    {
        var machinePath = Environment.GetEnvironmentVariable("PATH", EnvironmentVariableTarget.Machine) ?? "";
        var userPath    = Environment.GetEnvironmentVariable("PATH", EnvironmentVariableTarget.User) ?? "";

        Environment.SetEnvironmentVariable("PATH", $"{machinePath};{userPath}", EnvironmentVariableTarget.Process);
    }

    /// <summary>
    /// Runs an external process with the specified executable, arguments and working directory.
    /// The process output and error streams are redirected. If the process exits with a non-zero exit code,
    /// an exception is thrown with the executable name and exit code.
    /// </summary>
    /// <param name="exe"></param>
    /// <param name="args"></param>
    /// <param name="waitForExit"></param>
    /// <param name="workDir"></param>
    /// <param name="log"></param>
    /// <param name="shell"></param>
    /// <returns></returns>
    private Task RunProcess(string exe, string args, string? workDir = null, bool log = false, bool shell = false)
    {
        return Task.Run(() =>
        {
            
            using var p = new Process { StartInfo = BuildProcessInfo(exe, args, workDir ?? RepoRoot, shell) };

            if (log)
            {
                p.OutputDataReceived += (s, e) =>
                {
                    if (e.Data == null) return;
                    var logMessage = new Message(e.Data, DateTime.Now, "INFO");
                    _logger.LogNewMassage(logMessage);

                    Messages.Add(new LauncherMessage()
                    {
                        Message = e.Data,
                        Title = p.StartInfo.FileName,
                        Symbol = "✓"
                    });
                };

                p.ErrorDataReceived += (s, e) =>
                {
                    if (e.Data == null) return;
                    var logMessage = new Message(e.Data, DateTime.Now, "ERROR");
                    _logger.LogNewMassage(logMessage);

                    Messages.Add(new LauncherMessage()
                    {
                        Message = e.Data,
                        Title = p.StartInfo.FileName,
                        Symbol = "✗"
                    });
                };
            }

            p.Start();
            p.BeginOutputReadLine();
            p.BeginErrorReadLine();
            p.WaitForExit();

            if (p.ExitCode != 0)
                throw new Exception($"{Path.GetFileName(exe)} exited with code {p.ExitCode}");
        });
    }

    /// <summary>
    /// Creates a ProcessStartInfo configured for running a background process with redirected output and error
    /// streams, no shell execution, and no visible window. This is used by all process-launching methods in
    /// the launcher to ensure a consistent process configuration.
    /// </summary>
    /// <param name="exe"></param>
    /// <param name="args"></param>
    /// <param name="workDir"></param>
    /// <param name="shell"></param>
    /// <returns></returns>
    private static ProcessStartInfo BuildProcessInfo(string exe, string args, string workDir, bool shell) =>
        new()
        {
            FileName               = exe,
            Arguments              = args,
            WorkingDirectory       = workDir,
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = shell,
            CreateNoWindow         = true,
        };

    public class LauncherMessage
    {
        public string Message { get; set; }
        public string Title { get; set; }
        public string Symbol { get; set; }
    }
}