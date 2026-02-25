using System;
using System.Diagnostics;
using System.IO;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Data.Core;
using Avalonia.Data.Core.Plugins;
using System.Linq;
using Avalonia.Markup.Xaml;
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
            // Avoid duplicate validations from both Avalonia and the CommunityToolkit. 
            // More info: https://docs.avaloniaui.net/docs/guides/development-guides/data-validation#manage-validationplugins
            DisableAvaloniaDataAnnotationValidation();
            
            RunPsScript("StartServer.ps1"); // Start the local server when the application starts.
            
            desktop.Exit += OnExit; // Ensure the server is stopped when the application exits.
            
            desktop.MainWindow = new MainWindow
            {
                DataContext = new MainWindowViewModel(),
            };
        }

        base.OnFrameworkInitializationCompleted();
    }

    private void DisableAvaloniaDataAnnotationValidation()
    {
        // Get an array of plugins to remove
        var dataValidationPluginsToRemove =
            BindingPlugins.DataValidators.OfType<DataAnnotationsValidationPlugin>().ToArray();

        // remove each entry found
        foreach (var plugin in dataValidationPluginsToRemove)
        {
            BindingPlugins.DataValidators.Remove(plugin);
        }
    }
    
    private void RunPsScript(string scriptFile)
    {
        var exeDir = AppContext.BaseDirectory;

        // Hoch zum Repo-Root: net9.0 -> Debug -> bin -> PyScrapperDesktopApp -> (repo root)
        // Je nach Output-Struktur kann das 4–5 Parents sein. Stabiler: Script ins Output kopieren (siehe Fix B).
        var repoRoot = Directory.GetParent(exeDir)!.Parent!.Parent!.Parent!.Parent!.FullName;

        var psi = new ProcessStartInfo
        {
            FileName = "powershell.exe",
            Arguments = @$"-File {repoRoot}\LocalServer\scripts" + scriptFile,
            WorkingDirectory =  repoRoot,
            UseShellExecute = false,
            CreateNoWindow = false,
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