using System;
using System.Collections.Generic;
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
using Avalonia.Markup.Xaml;
using Avalonia.Styling;
using LibVLCSharp.Shared;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;
using PyScrapperDesktopApp.Views;
using Tmds.DBus.Protocol;

namespace PyScrapperDesktopApp;

public partial class App : Application
{
    private readonly AppLogger _logger = new AppLogger();

    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override async void OnFrameworkInitializationCompleted()
    {
        try
        {
            if (Design.IsDesignMode) return;

            base.OnFrameworkInitializationCompleted();

            var log = new Massage("Application initializing...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                desktop.ShutdownMode = ShutdownMode.OnExplicitShutdown;
                
                var settings = await DatabaseOperations.LoadSettings();
                var defaultSettings = new Settings();
                defaultSettings.SetDefaultSettings();

                AppData.Settings = settings ?? defaultSettings;

                RequestedThemeVariant = AppData.Settings.DarkModeEnabled ? ThemeVariant.Dark : ThemeVariant.Light;

                var launcher = new LauncherWindow();

                launcher.Closed += async (sender, args) =>
                {
                    switch (launcher.Result)
                    {
                        case LauncherResult.Success:
                            log = new Massage("Launcher completed successfully, loading application data...", DateTime.Now, "INFO");
                            _logger.LogNewMassage(log);

                            await LoadApplicationData(desktop);
                            break;

                        case LauncherResult.Cancelled:
                            log = new Massage("Launcher was cancelled by the user", DateTime.Now, "INFO");
                            _logger.LogNewMassage(log);
                            StopServer();
                            desktop.Shutdown(0);
                            break;

                        case LauncherResult.Error:
                        default:
                            log = new Massage("Launcher failed with an error", DateTime.Now, "ERROR");
                            _logger.LogNewMassage(log);
                            StopServer();
                            desktop.Shutdown(1);
                            break;
                    }
                };

                desktop.MainWindow = launcher;
            }
        }
        catch (Exception e)
        {
            var log = new Massage($"Application failed to start: {e.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                desktop.Shutdown(1);
            }
        }
    }

    private async Task LoadApplicationData(IClassicDesktopStyleApplicationLifetime desktop)
    {
        try
        {
            desktop.Exit += OnExit;

            var log = new Massage("Loading Data...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var medias = await DatabaseOperations.LoadDownloadedMediasNoDuplicates();

            var mediasToRemove = medias.Where(m => m.DownloadPath == "Does not exist").ToList();

            foreach (var media in medias)
            {
                media.SetTitle();

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
                        log = new Massage(
                            $"Media with id {media.Id} has an unsupported codec and will be set to not playable",
                            DateTime.Now, "WARNING");
                        _logger.LogNewMassage(log);
                    }
                }
            }

            foreach (var mediaToRemove in mediasToRemove)
            {
                medias.Remove(mediaToRemove);

                log = new Massage(
                    $"Media with id {mediaToRemove.Id} removed from the list because it does not exist",
                    DateTime.Now, "WARNING");
                _logger.LogNewMassage(log);
            }

            foreach (var media in medias)
            {
                AppData.AddDownloadedMedia(media);
            }

            var playlists = await DatabaseOperations.LoadPlaylistsNoDuplicates();

            foreach (var playlist in playlists)
            {
                AppData.AddPlaylist(playlist);
            }

            var diff = await ScanFolder(AppData.Settings.DownloadPath);

            log = new Massage($"Scanned download folder for new media, found {diff} new media items", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            log = new Massage(
                $"Application started with {AppData.DownloadedMedias.Count} listed medias and {AppData.PlayableMedias.Count} playable medias | deleted {mediasToRemove.Count} medias",
                DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            log = new Massage($"Application started with {AppData.Playlists.Count} playlists", DateTime.Now,
                "INFO");
            _logger.LogNewMassage(log);

            var mainWindow = new MainWindow();
            desktop.MainWindow = mainWindow;
            mainWindow.Show();

            desktop.ShutdownMode = ShutdownMode.OnMainWindowClose;
        }
        catch (Exception e)
        {
            var log = new Massage($"Application failed to load data: {e.Message}", DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            desktop.Shutdown(1);
        }
    }

    private void OnExit(object? sender, ControlledApplicationLifetimeExitEventArgs e)
    {
        var log = new Massage("Saving Data...", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        DatabaseOperations.SaveDownloadedMedias(AppData.DownloadedMedias);
        DatabaseOperations.SavePlaylists(AppData.Playlists);
        DatabaseOperations.SaveSettings(AppData.Settings);
        
        log = new Massage("Shutting down local server...", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        StopServer();
        
        log = new Massage("Local server is shutdown", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
    }

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

            foreach (var file in found)
            {
                var media = new DownloadedMedia(
                    url: "N/A",
                    mediaType: Path.GetExtension(file),
                    downloadedAt: DateTime.Now,
                    downloadPath: file,
                    isPlayable: false,
                    identifier: Guid.NewGuid().ToString()
                );
                media.SetTitle();
                media.SetHighestId(AppData.DownloadedMedias);
                
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

                int originalMediaCount = AppData.DownloadedMedias.Count;

                if (!alreadyExists)
                    AppData.AddDownloadedMedia(media);

                diff = AppData.DownloadedMedias.Count - originalMediaCount;

                return diff;
            }
        }
        catch (Exception ex)
        {
            var log = new Massage("An error occurred while scanning the folder: " + ex.Message, DateTime.Now, "ERROR");
            new AppLogger().LogNewMassage(log);
        }
        
        return 0;
    }

    public static void ToggleTheme()
    {
        AppData.Settings.DarkModeEnabled = !AppData.Settings.DarkModeEnabled;
        Current!.RequestedThemeVariant = AppData.Settings.DarkModeEnabled
            ? ThemeVariant.Dark
            : ThemeVariant.Light;
    }

    public static void StopServer()
    {
        try
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };
            http.PostAsync(
                "http://127.0.0.1:8765/command",
                new StringContent("{\"command\":\"quit\"}", Encoding.UTF8, "application/json")
            ).Wait();
        }
        catch
        {
            // Server was already stopped or unreachable
        }
    }
}