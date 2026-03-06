using System;
using System.Diagnostics;
using System.IO;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Data.Core;
using Avalonia.Data.Core.Plugins;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using Avalonia.Markup.Xaml;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;
using PyScrapperDesktopApp.Views;

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
        base.OnFrameworkInitializationCompleted();
        
        var log = new Massage("Application initializing...", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            DisableAvaloniaDataAnnotationValidation();
            
            log = new Massage("Installing frontend requirements", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            RunPsScript("InstallRequirementsFrontend.ps1", wait: true);
            
            log = new Massage("Frontend requirements installation completed", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            log = new Massage("Starting local server and installing requirements for backend", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            RunPsScript("StartServer.ps1");
            
            
            int maxTries = 30;
            int tries = 0;
            bool serverStarted = false;
            
            do
            {
                try
                {
                    await Task.Delay(1000);
                    var healthResponse = await new ApiClient().GetHealth("127.0.0.1:8765");

                    if (healthResponse.Ok)
                    {
                        serverStarted = true;
                    }
                
                }
                catch (Exception e)
                {
                    log = new Massage("Waiting for local server to start...", DateTime.Now, "INFO");
                    _logger.LogNewMassage(log);
                }
                tries ++;
            } while (!serverStarted && tries < maxTries);
            
            if (!serverStarted)
            {
                log = new Massage("Failed to start local server after multiple attempts", DateTime.Now, "ERROR");
                _logger.LogNewMassage(log);
                desktop.Shutdown(1);
                return;
            }
            
            log = new Massage("Local server started and backend requirements installation complete", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            desktop.Exit += OnExit;
            
            desktop.MainWindow = new MainWindow
            {
                DataContext = new MainWindowViewModel(),
            };
            
            var medias = DownloadedMedia.GetMediasFromJson(Path.Combine(AppData.DataPath, "downloadedMedias.json"));
            
            var mediasToRemove = medias.Where(m => m.DownloadPath == "Does not exist").ToList();

            if (mediasToRemove.Any())
            {
                foreach (var mediaToRemove in mediasToRemove)
                {
                    medias.Remove(mediaToRemove);
                    
                     log = new Massage($"Media with id {mediaToRemove.Id} removed from the list because it does not exist", DateTime.Now, "WARNING");
                    _logger.LogNewMassage(log);
                }
            }

            foreach (var media in medias)
            {
                if (File.Exists(media.DownloadPath))
                {
                    media.IsPlayable = true;
                }
                else
                {
                    media.IsPlayable = false;
                    media.DownloadPath = "Does not exist";
                }
                
                AppData.AddDownloadedMedia(media);
            }

            log = new Massage($"Application started with {AppData.DownloadedMedias.Count} listed medias and {AppData.PlayableMedias.Count} playable medias | deleted {mediasToRemove.Count} medias", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            desktop.MainWindow.Show();
        }
    }

    private void DisableAvaloniaDataAnnotationValidation()
    {
        var dataValidationPluginsToRemove =
            BindingPlugins.DataValidators.OfType<DataAnnotationsValidationPlugin>().ToArray();

        foreach (var plugin in dataValidationPluginsToRemove)
        {
            BindingPlugins.DataValidators.Remove(plugin);
        }
    }
    
    /// <summary>
    /// Finds the repo root by walking up from the exe directory until a folder
    /// containing "LocalServer" is found. Works from any build output location
    /// or if the exe is copied elsewhere — as long as it stays inside the repo.
    /// </summary>
    private static string FindRepoRoot()
    {
        var dir = new DirectoryInfo(AppContext.BaseDirectory);
        while (dir != null)
        {
            if (Directory.Exists(Path.Combine(dir.FullName, "LocalServer")))
                return dir.FullName;
            dir = dir.Parent;
        }
        throw new DirectoryNotFoundException(
            "Could not locate repo root (no 'LocalServer' folder found in any parent directory).");
    }

    /// <param name="scriptFile">Script filename only (e.g. "StartServer.ps1")</param>
    /// <param name="wait">If true, blocks until the script finishes.</param>
    private void RunPsScript(string scriptFile, bool wait = false)
    {
        var repoRoot = FindRepoRoot();

        var psi = new ProcessStartInfo
        {
            FileName = "powershell.exe",
            Arguments = $"-ExecutionPolicy Bypass -File \"{repoRoot}\\LocalServer\\scripts\\{scriptFile}\"",
            WorkingDirectory = repoRoot,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };

        var p = new Process { StartInfo = psi };
        p.Start();

        // Drain stdout/stderr asynchronously so the child process never
        // blocks on a full pipe buffer (classic deadlock cause).
        p.BeginOutputReadLine();
        p.BeginErrorReadLine();

        if (wait)
            p.WaitForExit();
    }

    private void OnExit(object? sender, ControlledApplicationLifetimeExitEventArgs e)
    {
        var log = new Massage("Shutting down local server...", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        RunPsScript("StopServer.ps1");
        
        log = new Massage("Local server is shutdown", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
    }
}