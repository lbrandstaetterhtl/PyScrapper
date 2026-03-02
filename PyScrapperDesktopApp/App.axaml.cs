using System;
using System.Diagnostics;
using System.IO;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Data.Core;
using Avalonia.Data.Core.Plugins;
using System.Linq;
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

    public override void OnFrameworkInitializationCompleted()
    {
        var log = new Massage("Application initializing...", DateTime.Now, "INFO");
        _logger.LogNewMassage(log);
        
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            DisableAvaloniaDataAnnotationValidation();
            
            log = new Massage("Local server starting...", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            
            RunPsScript("StartServer.ps1");
            
            log = new Massage("Local server started", DateTime.Now, "INFO");
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
                    
                     log = new Massage($"Media with id {mediaToRemove.Id} removed from the list because it does not exist at the specified path: {mediaToRemove.DownloadPath}", DateTime.Now, "WARNING");
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
        }

        base.OnFrameworkInitializationCompleted();
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
    
    private void RunPsScript(string scriptFile)
    {
        var exeDir = AppContext.BaseDirectory;

        var repoRoot = Directory.GetParent(exeDir)!.Parent!.Parent!.Parent!.Parent!.FullName;

        var psi = new ProcessStartInfo
        {
            FileName = "powershell.exe",
            Arguments = @$"-File {repoRoot}\LocalServer\scripts\" + scriptFile,
            WorkingDirectory =  repoRoot,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };

        var p = new Process { StartInfo = psi };
        p.Start();
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