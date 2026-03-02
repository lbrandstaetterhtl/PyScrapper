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
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            DisableAvaloniaDataAnnotationValidation();
            
            RunPsScript("StartServer.ps1");
            
            desktop.Exit += OnExit;
            
            desktop.MainWindow = new MainWindow
            {
                DataContext = new MainWindowViewModel(),
            };
            
            var medias = DownloadedMedia.GetMediasFromJson(Path.Combine(AppData.DataPath, "downloadedMedias.json"));

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
        RunPsScript("StopServer.ps1");
    }
}