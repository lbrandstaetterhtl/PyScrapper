using System;
using System.Diagnostics;
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
/// (backend packages, Playwright browsers, .NET packages), starting the Python backend server, and verifying
/// that the server is responsive. Once all steps have completed successfully, the window closes itself with
/// a Success result. If an error occurs at any point, the error is logged and displayed in the UI, and a
/// Close button becomes visible for the user to dismiss the window.
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
    private string _statusText = "Initializing...";

    [ObservableProperty]
    private bool _isLoading = true;

    [ObservableProperty]
    private bool _hasError = false;

    [ObservableProperty]
    private string _errorMessage = string.Empty;

    /// <summary>
    /// Constructor for the LauncherWindowViewModel. Checks for design mode to avoid executing runtime code in the designer.
    /// </summary>
    public LauncherWindowViewModel()
    {
        if (Design.IsDesignMode) return;
    }

    /// <summary>
    /// Method that is called when the launcher window is ready, which sets the window reference and starts
    /// the automatic launch sequence. The sequence checks if the server is already running, creates the
    /// Python virtual environment and installs dependencies if needed, restores .NET packages, starts the
    /// server, waits for a successful health check, and then closes the window with a Success result.
    /// If any step fails, the error is logged and displayed in the UI with a Close button.
    /// </summary>
    /// <param name="window"></param>
    public async void OnWindowReady(Window window)
    {
        _window = window;

        try
        {
            StatusText = "Checking for running server...";

            var log = new Massage("Checking if server is already running...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (await IsServerAlreadyRunning())
            {
                log = new Massage("Server is already running, skipping startup sequence", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                StatusText = "Server already running!";
                await FinishSuccess();
                return;
            }

            if (!File.Exists(VenvPython))
            {
                StatusText = "Creating Python environment...";

                log = new Massage("Creating Python virtual environment...", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await Task.Run(() => EnsureVenv());

                StatusText = "Upgrading pip...";

                log = new Massage("Upgrading pip...", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await RunProcess(VenvPython, "-m pip install --upgrade pip", LocalServer);

                StatusText = "Installing Python packages...";

                log = new Massage("Installing Python requirements...", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await RunProcess(VenvPython, $"-m pip install -r \"{Requirements}\"", LocalServer);

                StatusText = "Installing Playwright browsers...";

                log = new Massage("Installing Playwright browsers...", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                await RunProcess(VenvPython, "-m playwright install", LocalServer);
            }

            StatusText = "Restoring .NET packages...";

            log = new Massage("Restoring .NET packages...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            await RestoreDotnetPackages();

            StatusText = "Starting server...";

            log = new Massage("Starting local server...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            StartServerProcess();

            StatusText = "Waiting for server to respond...";

            log = new Massage("Waiting for server to respond...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            await WaitForServerReady();

            log = new Massage("Server started successfully", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            await FinishSuccess();
        }
        catch (Exception ex)
        {
            var log = new Massage($"Launcher error: {ex.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);

            ShowError(ex.Message);
        }
    }

    /// <summary>
    /// Method that is called when the launch sequence has completed successfully.
    /// It sets the status text to "Ready!", hides the progress bar, sets the launcher result to Success,
    /// briefly pauses so the user can see the final status, and then closes the window.
    /// </summary>
    private async Task FinishSuccess()
    {
        StatusText = "Ready!";
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
    private void ShowError(string message)
    {
        IsLoading = false;
        HasError = true;
        ErrorMessage = message;
        StatusText = "Launch failed";

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
    /// but not displayed in the UI since this is an automatic launcher without a log view.
    /// </summary>
    private void StartServerProcess()
    {
        var psi = BuildProcessInfo(
            VenvPython,
            "-m uvicorn LocalServer.server:app --host 127.0.0.1 --port 8765",
            RepoRoot
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
            StatusText = $"Restoring {Path.GetFileNameWithoutExtension(proj)}...";
            await RunProcess("dotnet", $"restore \"{proj}\"", RepoRoot);
        }
    }

    /// <summary>
    /// Ensures that a Python virtual environment exists at the expected path. If the venv does not exist,
    /// it searches for a Python installation on the system and creates one. If Python is not found or
    /// the venv creation fails, an exception is thrown.
    /// </summary>
    private void EnsureVenv()
    {
        if (File.Exists(VenvPython)) return;

        var venvDir = Path.Combine(LocalServer, ".venv");
        var python = FindPython() ?? throw new Exception("Python not found. Please install Python 3.12 and try again.");

        var p = Process.Start(BuildProcessInfo(python, $"-m venv \"{venvDir}\"", LocalServer))!;
        p.WaitForExit();

        if (!File.Exists(VenvPython))
            throw new Exception($"Failed to create virtual environment using: {python}");
    }

    /// <summary>
    /// Searches for a Python installation on the system by trying common executable names (py, python, python3).
    /// Returns the name of the first executable that responds to --version with exit code 0, or null if none is found.
    /// </summary>
    /// <returns></returns>
    private static string FindPython()
    {
        foreach (var name in new[] { "py", "python", "python3" })
        {
            try
            {
                var p = Process.Start(new ProcessStartInfo
                {
                    FileName               = name,
                    Arguments              = "--version",
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
    /// Runs an external process with the specified executable, arguments and working directory.
    /// The process output and error streams are redirected. If the process exits with a non-zero exit code,
    /// an exception is thrown with the executable name and exit code.
    /// </summary>
    /// <param name="exe"></param>
    /// <param name="args"></param>
    /// <param name="workDir"></param>
    /// <returns></returns>
    private Task RunProcess(string exe, string args, string workDir = null)
    {
        return Task.Run(() =>
        {
            using var p = new Process { StartInfo = BuildProcessInfo(exe, args, workDir ?? RepoRoot) };
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
    /// <returns></returns>
    private static ProcessStartInfo BuildProcessInfo(string exe, string args, string workDir) =>
        new()
        {
            FileName               = exe,
            Arguments              = args,
            WorkingDirectory       = workDir,
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        };
}
