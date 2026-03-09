using Avalonia;
using Avalonia.Headless;
using Avalonia.Themes.Fluent;

namespace PyScrapperDesktopApp.Tests;

/// <summary>
/// Initializes the Avalonia headless platform once for all tests that need it.
/// Use as [CollectionDefinition] + ICollectionFixture.
/// </summary>
public class AvaloniaFixture : IDisposable
{
    private static readonly object _lock = new();
    private static bool _initialized;

    public AvaloniaFixture()
    {
        lock (_lock)
        {
            if (!_initialized)
            {
                AppBuilder.Configure<TestApp>()
                    .UseHeadless(new AvaloniaHeadlessPlatformOptions())
                    .SetupWithoutStarting();
                _initialized = true;
            }
        }
    }

    public void Dispose() { }
}

public class TestApp : Application
{
    public override void Initialize()
    {
        Styles.Add(new FluentTheme());
    }
}

[CollectionDefinition("Avalonia")]
public class AvaloniaCollection : ICollectionFixture<AvaloniaFixture> { }

