using Avalonia;
using System;
using System.Threading.Tasks;
using LibVLCSharp.Shared;

namespace PyScrapperDesktopApp;

sealed class Program
{
    [STAThread]
    public static void Main(string[] args)
    {
        // Fängt ALLE Fehler ab, egal wo sie herkommen
        AppDomain.CurrentDomain.UnhandledException += (s, e) =>
        {
            var ex = e.ExceptionObject as Exception;
            try
            {
                System.IO.File.WriteAllText(
                    System.IO.Path.Combine(AppContext.BaseDirectory, "CRASH.txt"),
                    "UNHANDLED:\n" + (ex?.ToString() ?? "unknown"));
            }
            catch { }
        };

        try
        {
            var libVlcDir = System.IO.Path.Combine(AppContext.BaseDirectory, "libvlc", "win-x64");
            if (System.IO.Directory.Exists(libVlcDir))
                Core.Initialize(libVlcDir);
            else
                Core.Initialize();

            BuildAvaloniaApp()
                .StartWithClassicDesktopLifetime(args);
        }
        catch (Exception ex)
        {
            try
            {
                System.IO.File.WriteAllText(
                    System.IO.Path.Combine(AppContext.BaseDirectory, "CRASH.txt"),
                    "CAUGHT:\n" + ex.ToString());
            }
            catch { }
            throw;
        }
    }

    public static AppBuilder BuildAvaloniaApp()
        => AppBuilder.Configure<App>()
            .UsePlatformDetect()
            .WithInterFont()
            .LogToTrace();
}