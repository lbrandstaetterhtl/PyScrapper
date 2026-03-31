using System;
using System.Collections.ObjectModel;
using PyScrapperDesktopApp.Models;
using Xunit;

namespace PyScrapperDesktopApp.Tests.Models;

public class AppDataTests
{
    /// <summary>
    /// Reset static state before each test to avoid cross-test contamination.
    /// </summary>
    public AppDataTests()
    {
        AppData.DownloadedMedias.Clear();
        AppData.PlayableMedias.Clear();
    }

    [Fact]
    public void AddDownloadedMedia_PlayableMedia_AddsToDownloadedAndPlayable()
    {
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id1");

        AppData.AddDownloadedMedia(media);

        Assert.Single(AppData.DownloadedMedias);
        Assert.Single(AppData.PlayableMedias);
        Assert.Contains(media, AppData.DownloadedMedias);
        Assert.Contains(media, AppData.PlayableMedias);
    }

    [Fact]
    public void AddDownloadedMedia_NonPlayableMedia_AddsOnlyToDownloaded()
    {
        var media = new DownloadedMedia("url", ".mp4", DateTime.Now, "path", false, "id1");

        AppData.AddDownloadedMedia(media);

        Assert.Single(AppData.DownloadedMedias);
        Assert.Empty(AppData.PlayableMedias);
        Assert.Contains(media, AppData.DownloadedMedias);
    }

    [Fact]
    public void RemoveDownloadedMedia_PlayableMedia_RemovesFromBothCollections()
    {
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id1");
        AppData.AddDownloadedMedia(media);

        AppData.RemoveDownloadedMedia(media);

        Assert.Empty(AppData.DownloadedMedias);
        Assert.Empty(AppData.PlayableMedias);
    }

    [Fact]
    public void RemoveDownloadedMedia_NonPlayableMedia_RemovesOnlyFromDownloaded()
    {
        var playableMedia = new DownloadedMedia("url1", ".mp3", DateTime.Now, "path1", true, "id1");
        var nonPlayableMedia = new DownloadedMedia("url2", ".mp4", DateTime.Now, "path2", false, "id2");

        AppData.AddDownloadedMedia(playableMedia);
        AppData.AddDownloadedMedia(nonPlayableMedia);

        AppData.RemoveDownloadedMedia(nonPlayableMedia);

        Assert.Single(AppData.DownloadedMedias);
        Assert.Single(AppData.PlayableMedias);
        Assert.Contains(playableMedia, AppData.DownloadedMedias);
    }

    [Fact]
    public void AddMultipleMedias_CorrectCounts()
    {
        var m1 = new DownloadedMedia("url1", ".mp3", DateTime.Now, "p1", true, "id1");
        var m2 = new DownloadedMedia("url2", ".mp4", DateTime.Now, "p2", false, "id2");
        var m3 = new DownloadedMedia("url3", ".mp3", DateTime.Now, "p3", true, "id3");

        AppData.AddDownloadedMedia(m1);
        AppData.AddDownloadedMedia(m2);
        AppData.AddDownloadedMedia(m3);

        Assert.Equal(3, AppData.DownloadedMedias.Count);
        Assert.Equal(2, AppData.PlayableMedias.Count);
    }
}

