using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
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
    private static readonly AppLogger _logger = AppLogger.Instance;
    private static System.Diagnostics.Process? _serverProcess;

    /// <summary>
    /// Initializes the application by loading the XAML.
    /// </summary>
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        if (Design.IsDesignMode)
        {
            base.OnFrameworkInitializationCompleted();
            return;
        }

        base.OnFrameworkInitializationCompleted();

        if (ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
        {
            return;
        }

        // Dispatcher darf nicht sterben, solange wir noch Fenster zeigen wollen.
        desktop.ShutdownMode = ShutdownMode.OnExplicitShutdown;

        // Den async Startup-Flow erst starten, NACHDEM die Main-Loop läuft.
        // Post stellt die Arbeit in die Dispatcher-Queue - sie wird ausgeführt
        // sobald die Message-Loop aktiv ist, nicht vorher. Das verhindert den
        // "Dispatcher shut down" Crash im Release-Build.
        Avalonia.Threading.Dispatcher.UIThread.Post(async () =>
        {
            await StartupFlow(desktop);
        });
    }

    /// <summary>
    /// Der eigentliche asynchrone Startup-Ablauf: Login anzeigen, Settings laden,
    /// Theme setzen, Launcher öffnen. Läuft auf dem UI-Thread über den Dispatcher.
    /// </summary>
    private async Task StartupFlow(IClassicDesktopStyleApplicationLifetime desktop)
    {
        try
        {
            var log = new Message("Application initializing...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var config = AppConfig.Load();
            AppData.Config = config;

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

            var settings = await Database.LoadSettingsFromApiAsync();
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
                };

                settings = await Database.CreateSettingsAsync(settingReq);
            }

            AppData.Settings = settings;

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
            desktop.Shutdown(1);
        }
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

            var medias = await Database.LoadDownloadedMediasFromApiAsync() ?? new ObservableCollection<DownloadedMedia>();

            var mediasToRemove = medias.Where(m => m.DownloadPath == "Does not exist").ToList();
            mediasToRemove.AddRange(medias.Where(m => !File.Exists(m.DownloadPath)).ToList());
            
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

            var playlists = await Database.LoadPlaylistsFromApiAsync();

            foreach (var playlist in playlists)
            {
                await playlist.FindMedias();
                AppData.AddPlaylist(playlist);
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
    
    private void OnExit(object? sender, ControlledApplicationLifetimeExitEventArgs e)
    {
        try
        {
            bool ok = Task.Run(PerformExit).GetAwaiter().GetResult();
            e.ApplicationExitCode = ok ? 0 : 1;
        }
        catch (Exception ex)
        {
            _logger.LogNewMassage(new Message($"Fehler beim Exit: {ex.Message}", DateTime.Now, "ERROR"));
            e.ApplicationExitCode = 1;
        }
    }

    private async Task<bool> PerformExit()
    {
        try
        {
            var log = new Message("Saving Data...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var req = new SaveDataRequest()
            {
                UserIdentifier = AppData.CurrentUser.Identifier,
                Playlists = AppData.Playlists.ToList(),
                DownloadedMedias = AppData.DownloadedMedias.ToList(),
                PlaylistMedias = AppData.PlaylistMedias.ToList(),
                Setting = AppData.Settings
            };

            if (!await Database.SaveUserDataAsync(req))
            {
                log = new Message("Saving user data failed", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                return false;
            }
            
            log = new Message("Saved user data successfully", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            var client = new ApiClient();
            
            var loggedOut = await client.Logout();
            if (!loggedOut)
            {
                log = new Message("User logout failed", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                return false;
            }
            
            log = new Message("User logged out successfully", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            AppData.Config.LastLoggedInUser = AppData.CurrentUser;
            AppConfig.Save(AppData.Config);
        
            return true;
        }
        catch (Exception ex)
        {
            var log = new Message("An error occurred while saving data: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return false;
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
                    Title = Path.GetFileNameWithoutExtension(file),
                    IsPlayable = true,
                };
                
                if (AppData.MediaAlreadyExists(file))
                    continue;

                var media = await Database.CreateDownloadedMediaAsync(req);

                bool exists = File.Exists(media.DownloadPath);

                if (exists)
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
            _logger.LogNewMassage(log);
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
    
    /// <summary>
    /// Locates the ffprobe executable by checking PATH first, then the WinGet yt-dlp.FFmpeg package
    /// directory, and finally the local ffmpeg folder placed by the launcher. This mirrors the lookup
    /// logic of the Python find_ffmpeg() function so both sides of the application agree on the location.
    /// Returns the full path to ffprobe.exe, or null if it cannot be found.
    /// </summary>
    public static string? FindExe(string name)
    {
        var where = Process.Start(new ProcessStartInfo
        {
            FileName               = "where",
            Arguments              = name,
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        })!;
        var result = where.StandardOutput.ReadToEnd().Trim();
        where.WaitForExit();
        if (where.ExitCode == 0 && !string.IsNullOrEmpty(result))
            return result.Split('\n')[0].Trim();

        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var pkgRoot = Path.Combine(localAppData, "Microsoft", "WinGet", "Packages");
        if (Directory.Exists(pkgRoot))
        {
            var hit = Directory
                .EnumerateFiles(pkgRoot, "ffprobe.exe", SearchOption.AllDirectories)
                .FirstOrDefault(f => f.Contains("yt-dlp.FFmpeg"));
            if (hit != null) return hit;
        }

        var localFfprobe = Path.Combine(AppData.PyScrapperPath, "LocalServer", "ffmpeg", "bin", "ffprobe.exe");
        if (File.Exists(localFfprobe)) return localFfprobe;

        return null;
    }
}