using Avalonia;
using Avalonia.Headless;
using Avalonia.Themes.Fluent;
using Xunit;

[assembly: CollectionBehavior(DisableTestParallelization = true)]

namespace PyScrapperDesktopApp.Tests;

/// <summary>
/// Initializes the Avalonia headless platform once for all tests that need it.
/// </summary>
public class AvaloniaFixture 
{
    // Keeping it mostly empty as Avalonia.Headless.XUnit handles most logic via AvaloniaFact
}

public class TestApp : Application
{
    public override void Initialize()
    {
        Styles.Add(new FluentTheme());
    }

    public static AppBuilder BuildAvaloniaApp() => AppBuilder.Configure<TestApp>()
        .UseSkia()
        .UseHeadless(new AvaloniaHeadlessPlatformOptions
        {
            UseHeadlessDrawing = true
        })
        .WithInterFont();
}

[CollectionDefinition("Avalonia")]
public class AvaloniaCollection : ICollectionFixture<AvaloniaFixture> { }

