using System.IO;
using PyScrapperDesktopApp.Models;
using Xunit;

namespace PyScrapperDesktopApp.Tests.Models;

public class SettingsTests
{
    [Fact]
    public void Constructor_SetsDefaultValues()
    {
        var settings = new Settings();

        Assert.Equal(1, settings.Id);
        Assert.Null(settings.DownloadPath);
        Assert.False(settings.DarkModeEnabled);
        Assert.Equal("http://127.0.0.1:8765", settings.ServerUrl);
    }

    [Fact]
    public void ServerUrl_ReturnsCorrectValue()
    {
        var settings = new Settings();

        Assert.Equal("http://127.0.0.1:8765", settings.ServerUrl);
    }

    [Fact]
    public void SetDefaultSettings_SetsDownloadPath()
    {
        var settings = new Settings();

        settings.SetDefaultSettings();

        Assert.NotNull(settings.DownloadPath);
        Assert.True(settings.DarkModeEnabled);
        Assert.True(settings.DownloadPath.EndsWith("Downloads"));
    }

    [Fact]
    public void SetDefaultSettings_DownloadPathContainsDownloadsFolder()
    {
        var settings = new Settings();

        settings.SetDefaultSettings();

        Assert.EndsWith("Downloads", settings.DownloadPath);
    }

    [Fact]
    public void DarkModeEnabled_CanBeToggled()
    {
        var settings = new Settings();

        Assert.False(settings.DarkModeEnabled);

        settings.DarkModeEnabled = true;
        Assert.True(settings.DarkModeEnabled);

        settings.DarkModeEnabled = false;
        Assert.False(settings.DarkModeEnabled);
    }

    [Fact]
    public void DownloadPath_CanBeModified()
    {
        var settings = new Settings();
        var customPath = @"C:\Custom\Download\Path";

        settings.DownloadPath = customPath;

        Assert.Equal(customPath, settings.DownloadPath);
    }
}


