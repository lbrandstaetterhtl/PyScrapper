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
    private readonly AppLogger _logger = new AppLogger();

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

    /// <summary>
    /// Constructor for the LauncherWindowViewModel. Checks for design mode to avoid executing runtime code in the designer.
    /// </summary>
    public LauncherWindowViewModel()
    {
        if (Design.IsDesignMode) return;
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

            var log = new Massage("Checking if server is already running...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (await IsServerAlreadyRunning())
            {
                log = new Massage("Server is already running, skipping startup sequence", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await Dispatcher.UIThread.InvokeAsync(() =>
                {
                    Messages.Add(new LauncherMessage()
                    {
                        Message = "is already running",
                        Title = "Server",
                        Symbol = "✗"
                    });
                });

                await FinishSuccess();
                return;
            }

            await Task.WhenAll(
                Task.Run(EnsureVcRedist),
                Task.Run(EnsureFfmpeg),
                Task.Run(EnsurePython),
                Task.Run(EnsureVenv),
                Task.Run(() => { RunProcess("python", "-m pip install --upgrade pip", LocalServer).Wait();}),
                Task.Run(() => {RunProcess("python", $"-m pip install -r \"{Requirements}\"", LocalServer).Wait(); }),
                Task.Run(() => RunProcess(VenvPython, " -m playwright install", LocalServer).Wait() ),
                RestoreDotnetPackages()
            );
            
            StartServerProcess();
            
            await WaitForServerReady();

            await FinishSuccess();
        }
        catch (Exception ex)
        {
            var log = new Massage($"Launcher error: {ex.Message}", DateTime.Now, "ERROR");
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
    private async Task<bool> IsServerAlreadyRunning()
    {
        try
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
            var response = await http.GetAsync("http://127.0.0.1:8765/docs");
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Starts the Python uvicorn server as a background process. The process is kept alive and referenced
    /// by the _serverProcess field so it can be cleaned up if needed. Output and error streams are redirected
    /// and logged so that server startup errors are visible in the application log.
    /// </summary>
    private void StartServerProcess()
    {
        var psi = BuildProcessInfo(
            VenvPython,
            "-m uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765",
            RepoRoot,
            false
        );

        _serverProcess = new Process { StartInfo = psi };

        _serverProcess.Start();
        _serverProcess.BeginOutputReadLine();
        _serverProcess.BeginErrorReadLine();
    }

    /// <summary>
    /// Waits for the server to respond to HTTP requests by polling the docs endpoint every second.
    /// If the server does not respond within 30 seconds, or if the server process exits unexpectedly,
    /// an exception is thrown which is caught by the calling method and displayed as an error in the UI.
    /// </summary>
    /// <returns></returns>
    private async Task WaitForServerReady()
    {
        using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };

        for (int attempt = 0; attempt < 30; attempt++)
        {
            if (_serverProcess != null && _serverProcess.HasExited)
                throw new Exception($"Server process exited unexpectedly (Exit Code: {_serverProcess.ExitCode}).");

            try
            {
                var response = await http.GetAsync("http://127.0.0.1:8765/docs");
                if (response.IsSuccessStatusCode) return;
            }
            catch { }

            await Task.Delay(1000);
        }

        throw new Exception("Server did not respond within 30 seconds. Check your Python environment and server logs.");
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

            var log = new Massage("VCRUNTIME140.dll found, skipping Visual C++ Redistributable install", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            return;
        }

        var warnLog = new Massage("VCRUNTIME140.dll not found, downloading Visual C++ Redistributable...", DateTime.Now, "WARN");
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

        var doneLog = new Massage("Visual C++ Redistributable installed successfully", DateTime.Now, "INFO");
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

            var log = new Massage("ffmpeg found, skipping install", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            return;
        }

        var warnLog = new Massage("ffmpeg not found, installing via WinGet (yt-dlp.FFmpeg)...", DateTime.Now, "WARN");
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

        var doneLog = new Massage("ffmpeg installed successfully via WinGet", DateTime.Now, "INFO");
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
    /// Verifies that a compatible Python executable (3.12 or lower) is available on the system.
    /// Python 3.13 and above are rejected because key dependencies such as greenlet and playwright
    /// do not yet provide binary wheels for those versions, which causes DLL load failures at runtime.
    /// If no compatible Python is found or the version is too new, an exception is thrown with
    /// instructions for the user.
    /// </summary>
    private async Task EnsurePython()
    {

            var python = FindPython();

            if (python != null)
            {
                await Dispatcher.UIThread.InvokeAsync(() => Messages.Add(new LauncherMessage
                {
                    Message = $"Found {python.Split(' ')[0]} executable",
                    Title = "Python",
                    Symbol = "✓"
                }));
                return;
            }

            await Dispatcher.UIThread.InvokeAsync(() => Messages.Add(new LauncherMessage()
            {
                Message = "3.12 not found | downloading installer",
                Title = "Python",
                Symbol = "⏳"
            }));

            using var httpClient = new HttpClient();
            var bytes = await httpClient.GetByteArrayAsync(_installerUrl);
            await File.WriteAllBytesAsync(_installerPath, bytes);

            await Dispatcher.UIThread.InvokeAsync(() => Messages.Add(new LauncherMessage()
            {
                Message = $"Installing (admins right required)",
                Title = "Python",
                Symbol = "⏳"
            }));

            await RunProcess(_installerPath, "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0", null, log: true, shell: true);

            await Dispatcher.UIThread.InvokeAsync(() => Messages.Add(new LauncherMessage()
            {
                Message = "Installation complete, verifying...",
                Title = "Python",
                Symbol = "⏳"
            }));
            
            RefreshEnvironmentPath();
            
            python = FindPython();

            if (python == null)
            {
                throw new Exception(
                    "Python 3.12 executable not found after installation. Please ensure Python 3.12 is installed and added to PATH, then restart the application.\n" +
                    "You can download it from: https://www.python.org/downloads/release/python-3120/"
                );
            }
            
            await Dispatcher.UIThread.InvokeAsync(() => Messages.Add(new LauncherMessage()
            {
                Message = $"Found {python.Split(' ')[0]} executable after installation",
                Title = "Python",
                Symbol = "✓"
            }));    
    }

    /// <summary>
    /// Ensures that a Python virtual environment exists at the expected path. If the venv does not exist,
    /// it searches for a compatible Python installation, checks that pip is available via ensurepip if
    /// needed, and creates the virtual environment. If the venv already exists, this method returns
    /// immediately without recreating it. If Python is not found, pip cannot be bootstrapped, or the
    /// venv creation fails, an exception is thrown.
    /// </summary>
    private void EnsureVenv()
    {
        if (File.Exists(VenvPython)) return;

        var venvDir = Path.Combine(LocalServer, ".venv");
        var python  = FindPython() ?? throw new Exception("Python not found. Please install Python 3.12 and try again.");
        var exe     = python.Split(' ')[0];
        var args    = python.Contains(' ') ? python.Split(' ', 2)[1] : string.Empty;

        EnsurePipAvailable(exe, args);

        var venvArgs = string.IsNullOrEmpty(args)
            ? $"-m venv \"{venvDir}\""
            : $"{args} -m venv \"{venvDir}\"";

        var p = Process.Start(BuildProcessInfo(exe, venvArgs, LocalServer, false))!;
        p.WaitForExit();

        if (!File.Exists(VenvPython))
            throw new Exception($"Failed to create virtual environment using: {python}");
    }

    /// <summary>
    /// Checks if pip is available for the given Python executable by running pip --version.
    /// If pip is not found, attempts to bootstrap it using the built-in ensurepip module.
    /// If ensurepip also fails, an exception is thrown with platform-specific installation instructions.
    /// This method may run on a background thread and uses Dispatcher.UIThread.Post to update the status text.
    /// </summary>
    /// <param name="exe"></param>
    /// <param name="extraArgs"></param>
    private void EnsurePipAvailable(string exe, string extraArgs)
    {
        var pipArgs = string.IsNullOrEmpty(extraArgs)
            ? "-m pip --version"
            : $"{extraArgs} -m pip --version";

        var check = Process.Start(new ProcessStartInfo
        {
            FileName               = exe,
            Arguments              = pipArgs,
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        })!;
        check.WaitForExit();

        if (check.ExitCode == 0) return;

        var log = new Massage("pip not found, attempting bootstrap via ensurepip...", DateTime.Now, "WARN");
        _logger.LogNewMassage(log);

        Dispatcher.UIThread.Post(() => Messages.Add(new LauncherMessage()
        {
            Message = "bootstrapping pip...",
            Title = "pip Check",
            Symbol = "✓"
        }));

        var ensureArgs = string.IsNullOrEmpty(extraArgs)
            ? "-m ensurepip --upgrade"
            : $"{extraArgs} -m ensurepip --upgrade";

        var bootstrap = Process.Start(new ProcessStartInfo
        {
            FileName               = exe,
            Arguments              = ensureArgs,
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        })!;
        bootstrap.WaitForExit();

        if (bootstrap.ExitCode != 0)
            throw new Exception(
                "pip is not installed and could not be bootstrapped automatically.\n" +
                "On Debian/Ubuntu: sudo apt install python3-pip\n" +
                "On Arch: sudo pacman -S python-pip"
            );
    }

    /// <summary>
    /// Searches for a compatible Python 3.12 installation on the system by trying version-specific
    /// executable names first (py -3.12, python3.12) before falling back to generic names.
    /// Returns the full invocation string (e.g. "py -3.12") of the first executable that responds
    /// to --version with exit code 0, or null if none is found.
    /// </summary>
    /// <returns></returns>
    private static string FindPython()
    {
        foreach (var name in new[] { "py -3.12", "python3.12", "py", "python", "python3" })
        {
            try
            {
                var parts = name.Split(' ', 2);
                var p = Process.Start(new ProcessStartInfo
                {
                    FileName               = parts[0],
                    Arguments              = parts.Length > 1 ? parts[1] + " --version" : "--version",
                    RedirectStandardOutput = true,
                    RedirectStandardError  = true,
                    UseShellExecute        = false,
                    CreateNoWindow         = true,
                });
                p?.WaitForExit();
                if (p?.ExitCode == 0) return name;
            }
            catch { }
        }
        return null;
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
                    var logMessage = new Massage(e.Data, DateTime.Now, "INFO");
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
                    var logMessage = new Massage(e.Data, DateTime.Now, "ERROR");
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