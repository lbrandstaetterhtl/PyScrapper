using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Data.Core;
using Avalonia.Data.Core.Plugins;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.Documents;
using Avalonia.Logging;
using Avalonia.Markup.Xaml;
using Avalonia.Styling;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;
using PyScrapperDesktopApp.Views;
using Tmds.DBus.Protocol;
using Message = PyScrapperDesktopApp.Models.Message;

namespace PyScrapperDesktopApp;

/// <summary>
/// The main Application class for PyScrapperDesktopApp. Handles initialization, 
/// startup lifecycle, loading of user settings, database initialization, 
/// directory scanning, and orderly shutdown processes including stopping the local server.
/// </summary>
public partial class App : Application
{
    private readonly AppLogger _logger = new AppLogger();
    private static System.Diagnostics.Process? _serverProcess;

    /// <summary>
    /// Initializes the application by loading the XAML.
    /// </summary>
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    /// <summary>
    /// Called when the framework initialization is completed. 
    /// Starts the local server, waits for it to be ready, shows the LoginWindow and waits for it 
    /// to close, then loads settings, sets the visual theme, and opens the LauncherWindow 
    /// to begin the data loading process.
    /// </summary>
    public override async void OnFrameworkInitializationCompleted()
    {
        try
        {
            if (Design.IsDesignMode) return;

            base.OnFrameworkInitializationCompleted();

            var log = new Message("Application initializing...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            {
                return;
            }

            desktop.ShutdownMode = ShutdownMode.OnExplicitShutdown;

            /*
            // --- Lokalen Server starten ---
            StartLocalServer();

            // --- Warten, bis der Server tatsächlich erreichbar ist ---
            log = new Massage("Waiting for local server to become ready...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            bool serverReady = await WaitForServerReady("http://127.0.0.1:8765");

            if (!serverReady)
            {
                log = new Massage("Local server did not start in time, shutting down", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                desktop.Shutdown(1);
                return;
            }

            log = new Massage("Local server is ready", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            */

            // --- Login-Fenster zeigen und wirklich darauf warten (ShowDialog geht hier nicht, kein Owner vorhanden) ---
            
            var loginWindow = new LoginWindow();
            desktop.MainWindow = loginWindow;

            var loginTcs = new TaskCompletionSource<LoginResult>();
            loginWindow.Closed += (sender, args) => loginTcs.TrySetResult(loginWindow.Result);
            loginWindow.Show();

            var loginResult = await loginTcs.Task;

            if (loginResult != LoginResult.Success || AppData.CurrentUser == null)
            {
                log = new Message("Login was cancelled or failed, shutting down", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
                desktop.Shutdown(0);
                return;
            }

            var settings = await Database.LoadSettingsFromApi();
            if (settings == null)
            {
                log = new Message("Failed to load settings from database, using default settings", DateTime.Now, "WARN");
                _logger.LogNewMassage(log);

                var settingReq = new CreateSettingRequest
                {
                    DefaultDownloadPath = AppData.PyScrapperPath,
                    DarkModeEnabled = false,
                    ScanFolderOnStartup = true,
                    UserIdentifier = AppData.CurrentUser.Identifier,
                    ServerUrl = "http://127.0.0.1:8765",
                };

                settings = await Database.CreateSettings(settingReq);
            }

            AppData.Settings = settings ;

            RequestedThemeVariant = AppData.Settings.DarkModeEnabled ? ThemeVariant.Dark : ThemeVariant.Light;

            var launcher = new LauncherWindow();

            launcher.Closed += async (sender, args) =>
            {
                switch (launcher.Result)
                {
                    case LauncherResult.Success:
                        log = new Message("Launcher completed successfully, loading application data...", DateTime.Now, "INFO");
                        _logger.LogNewMassage(log);

                        await LoadApplicationData(desktop);
                        break;

                    case LauncherResult.Cancelled:
                        log = new Message("Launcher was cancelled by the user", DateTime.Now, "INFO");
                        _logger.LogNewMassage(log);
                        desktop.Shutdown(0);
                        break;

                    case LauncherResult.Error:
                    default:
                        log = new Message("Launcher failed with an error", DateTime.Now, "ERROR");
                        _logger.LogNewMassage(log);
                        desktop.Shutdown(1);
                        break;
                }
            };

            desktop.MainWindow = launcher;
            launcher.Show();
        }
        catch (Exception e)
        {
            var log = new Message($"Application failed to start: {e.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                desktop.Shutdown(1);
            }
        }
    }

    /// <summary>
    /// Starts the local Python FastAPI server as a subprocess, using the interpreter 
    /// from the project's virtual environment. Redirects stdout/stderr into the app log.
    /// </summary>
    private static void StartLocalServer()
    {
        var logger = new AppLogger();

        string pythonPath = Path.Combine(AppData.PyScrapperPath, "LocalServer", ".venv", "Scripts", "python.exe");

        if (!File.Exists(pythonPath))
        {
            var errorLog = new Message($"Python venv not found at expected path: {pythonPath}", DateTime.Now, "ERROR");
            logger.LogNewMassage(errorLog);
            throw new FileNotFoundException($"Python venv not found at: {pythonPath}");
        }

        _serverProcess = new System.Diagnostics.Process
        {
            StartInfo = new System.Diagnostics.ProcessStartInfo
            {
                FileName = pythonPath,
                Arguments = "-m uvicorn server:app --host 127.0.0.1 --port 8765",
                WorkingDirectory = Path.Combine(AppData.PyScrapperPath, "LocalServer"),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            }
        };

        _serverProcess.OutputDataReceived += (sender, e) =>
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                var log = new Message($"[Server] {e.Data}", DateTime.Now, "INFO");
                logger.LogNewMassage(log);
            }
        };

        _serverProcess.ErrorDataReceived += (sender, e) =>
        {
            if (!string.IsNullOrEmpty(e.Data))
            {
                var log = new Message($"[Server ERROR] {e.Data}", DateTime.Now, "ERROR");
                logger.LogNewMassage(log);
            }
        };

        _serverProcess.Start();
        _serverProcess.BeginOutputReadLine();
        _serverProcess.BeginErrorReadLine();
    }

    /// <summary>
    /// Polls the given base URL until it responds successfully or the maximum number 
    /// of attempts is reached. Used to ensure the local server is up before making API calls.
    /// </summary>
    private static async Task<bool> WaitForServerReady(string baseUrl, int maxAttempts = 40)
    {
        using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };

        for (int i = 0; i < maxAttempts; i++)
        {
            try
            {
                var response = await client.GetAsync($"{baseUrl}/");
                if (response.IsSuccessStatusCode)
                    return true;
            }
            catch
            {
                // Server noch nicht bereit, weiter versuchen
            }

            await Task.Delay(250);
        }

        return false;
    }

    /// <summary>
    /// Loads core application data including downloaded medias and playlists from the database. 
    /// Performs file existence checks, validates media codecs, scans the download directory for new files, 
    /// and finally launches the MainWindow.
    /// </summary>
    /// <param name="desktop">The application lifetime object.</param>
    private async Task LoadApplicationData(IClassicDesktopStyleApplicationLifetime desktop)
    {
        try
        {
            desktop.Exit += OnExit;

            var log = new Message("Loading Data...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var medias = await Database.LoadDownloadedMediasFromApi() ?? new ObservableCollection<DownloadedMedia>();

            var mediasToRemove = medias.Where(m => m.DownloadPath == "Does not exist").ToList();

            foreach (var media in medias)
            {
                bool exists = File.Exists(media.DownloadPath);
                bool isSupported = false;
                if (exists)
                {
                    isSupported = !media.DownloadPath.EndsWith(".mp4") || await AudioPlayer.IsSupportedCodec(media.DownloadPath);
                }

                if (exists && isSupported)
                {
                    media.IsPlayable = true;
                }
                else
                {
                    media.IsPlayable = false;

                    if (!exists)
                    {
                        mediasToRemove.Add(media);
                    }
                    else
                    {
                        log = new Message(
                            $"Media with id {media.Identifier} has an unsupported codec and will be set to not playable",
                            DateTime.Now, "WARN");
                        _logger.LogNewMassage(log);
                    }
                }
            }

            foreach (var mediaToRemove in mediasToRemove)
            {
                medias.Remove(mediaToRemove);

                log = new Message(
                    $"Media with id {mediaToRemove.Identifier} removed from the list because it does not exist",
                    DateTime.Now, "WARN");
                _logger.LogNewMassage(log);
            }

            foreach (var media in medias)
            {
                AppData.AddDownloadedMedia(media);
            }

            var playlists = await Database.LoadPlaylistsFromApi();

            foreach (var playlist in playlists)
            {
                AppData.AddPlaylist(playlist);
            }
            
            foreach (var playlist in playlists)
            {
                var playlistMedias = await Database.LoadPlaylistMediaFromApi(playlist.Identifier);

                foreach (var media in playlistMedias)
                {
                    AppData.PlaylistMedias.Add(media);
                }
                
                playlist.FindMedias();
            }

            if (AppData.Settings.ScanFolderOnStartup)
            {
                var diff = await ScanFolder(AppData.Settings.DownloadPath);

                log = new Message($"Scanned download folder for new media, found {diff} new media items", DateTime.Now,
                    "INFO");
                _logger.LogNewMassage(log);
            }

            log = new Message(
                $"Application started with {AppData.DownloadedMedias.Count} listed medias and {AppData.PlayableMedias.Count} playable medias | deleted {mediasToRemove.Count} medias",
                DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            log = new Message($"Application started with {AppData.Playlists.Count} playlists", DateTime.Now,
                "INFO");
            _logger.LogNewMassage(log);

            var mainWindow = new MainWindow();
            desktop.MainWindow = mainWindow;
            mainWindow.Show();

            desktop.ShutdownMode = ShutdownMode.OnMainWindowClose;
        }
        catch (Exception e)
        {
            var log = new Message($"Application failed to load data: {e.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            desktop.Shutdown(1);
        }
    }

    /// <summary>
    /// Triggered upon application exit. Saves the current state of downloaded medias, 
    /// playlists, and settings back to the database, and shuts down the local Python API server.
    /// </summary>
    /// <param name="sender">Event sender.</param>
    /// <param name="e">Event arguments.</param>
    private async void OnExit(object? sender, ControlledApplicationLifetimeExitEventArgs e)
    {
        try
        {
            var log = new Message("Saving Data...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var desktop = ApplicationLifetime as IClassicDesktopStyleApplicationLifetime;

            var req = new SaveDataRequest()
            {
                UserIdentifier = AppData.CurrentUser.Identifier,
                Playlists = AppData.Playlists.ToList(),
                DownloadedMedias = AppData.DownloadedMedias.ToList(),
                PlaylistMedias = AppData.PlaylistMedias.ToList(),
                Setting = AppData.Settings
            };

            await Database.SaveUserData(req);
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while saving data: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }

    /// <summary>
    /// Scans the given folder for media files (e.g., .mp3, .mp4) and registers any new items 
    /// that are not already present in the AppData media list. Returns the number of new medias added.
    /// </summary>
    /// <param name="folder">The folder to scan.</param>
    /// <returns>The number of new files added.</returns>
    public static async Task<int> ScanFolder(string folder)
    {
        var diff = 0;
        if (Current.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop) return diff;

        try
        {
            var extensions = new[]
            {
                ".mp3",
                ".mp4"
            };

            if (!Directory.Exists(folder))
                return diff;

            var found = Directory.EnumerateFiles(folder, "*", SearchOption.AllDirectories)
                .Where(f => extensions.Contains(Path.GetExtension(f)));

            int originalMediaCount = AppData.DownloadedMedias.Count;

            foreach (var file in found)
            {
                var req = new CreateDownloadedMediaRequest
                {
                    DownloadPath = file,
                    UserIdentifier = AppData.CurrentUser.Identifier,
                    DownloadedAt = File.GetCreationTime(file).ToString("O"),
                    MediaType = Path.GetExtension(file),
                    Url = "N/A",
                    Title = Path.GetFileName(file),
                    IsPlayable = true,
                };
                
                if (AppData.MediaAlreadyExists(file))
                    continue;

                var media = await Database.CreateDownloadedMedia(req);

                bool exists = File.Exists(media.DownloadPath);
                bool isSupported = false;
                if (exists)
                {
                    isSupported = !media.DownloadPath.EndsWith(".mp4") || await AudioPlayer.IsSupportedCodec(media.DownloadPath);
                }

                if (exists && isSupported)
                {
                    media.IsPlayable = true;
                }

                bool alreadyExists = AppData.MediaAlreadyExists(file);

                if (!alreadyExists)
                    AppData.AddDownloadedMedia(media);
            }

            diff = AppData.DownloadedMedias.Count - originalMediaCount;

            return diff;
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while scanning the folder: " + ex.Message, DateTime.Now, "ERROR");
            new AppLogger().LogNewMassage(log);
        }

        return 0;
    }

    /// <summary>
    /// Toggles the application's visual theme between Light and Dark mode, 
    /// updating the centralized settings and applying the change to the UI.
    /// </summary>
    public static void ToggleTheme()
    {
        AppData.Settings.DarkModeEnabled = !AppData.Settings.DarkModeEnabled;
        Current!.RequestedThemeVariant = AppData.Settings.DarkModeEnabled
            ? ThemeVariant.Dark
            : ThemeVariant.Light;
    }
}