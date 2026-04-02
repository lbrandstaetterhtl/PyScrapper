using System;
using System.Collections.ObjectModel;
using System.IO;
using PyScrapperDesktopApp.Models;
using Xunit;

namespace PyScrapperDesktopApp.Tests.Models;

public class DownloadedMediaTests
{
    [Fact]
    public void Constructor_SetsAllPropertiesCorrectly()
    {
        var url = "https://example.com/video";
        var mediaType = ".mp3";
        var downloadedAt = new DateTime(2025, 6, 1, 12, 0, 0);
        var downloadPath = @"C:\Downloads\test.mp3";
        var isPlayable = true;
        var identifier = "abc123";

        var media = new DownloadedMedia(url, mediaType, downloadedAt, downloadPath, isPlayable, identifier);

        Assert.Equal(url, media.Url);
        Assert.Equal(mediaType, media.MediaType);
        Assert.Equal(downloadedAt, media.DownloadedAt);
        Assert.Equal(downloadPath, media.DownloadPath);
        Assert.True(media.IsPlayable);
        Assert.Equal(identifier, media.Identifier);
    }

    [Fact]
    public void SetHighestId_EmptyCollection_SetsIdTo1()
    {
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id1");
        var collection = new ObservableCollection<DownloadedMedia>();

        media.SetHighestId(collection);

        Assert.Equal(1, media.Id);
    }

    [Fact]
    public void SetHighestId_CollectionWithItems_SetsIdToMaxPlusOne()
    {
        var existing1 = new DownloadedMedia("url1", ".mp3", DateTime.Now, "path1", true, "id1") { Id = 3 };
        var existing2 = new DownloadedMedia("url2", ".mp4", DateTime.Now, "path2", false, "id2") { Id = 7 };
        var existing3 = new DownloadedMedia("url3", ".mp3", DateTime.Now, "path3", true, "id3") { Id = 5 };

        var collection = new ObservableCollection<DownloadedMedia> { existing1, existing2, existing3 };

        var newMedia = new DownloadedMedia("url4", ".mp3", DateTime.Now, "path4", true, "id4");
        newMedia.SetHighestId(collection);

        Assert.Equal(8, newMedia.Id);
    }

    [Fact]
    public void SetHighestId_SingleItemCollection_SetsIdToItemIdPlusOne()
    {
        var existing = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id1") { Id = 1 };
        var collection = new ObservableCollection<DownloadedMedia> { existing };

        var newMedia = new DownloadedMedia("url2", ".mp3", DateTime.Now, "path2", true, "id2");
        newMedia.SetHighestId(collection);

        Assert.Equal(2, newMedia.Id);
    }

    [Fact]
    public void Properties_CanBeModifiedAfterConstruction()
    {
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id");

        media.Id = 42;
        media.Url = "new-url";
        media.MediaType = ".mp4";
        media.DownloadPath = "new-path";
        media.IsPlayable = false;
        media.Identifier = "new-id";

        Assert.Equal(42, media.Id);
        Assert.Equal("new-url", media.Url);
        Assert.Equal(".mp4", media.MediaType);
        Assert.Equal("new-path", media.DownloadPath);
        Assert.False(media.IsPlayable);
        Assert.Equal("new-id", media.Identifier);
    }

    [Fact]
    public void SetTitle_ExtractsFileNameWithoutExtension()
    {
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, @"C:\Downloads\my-song.mp3", true, "id");

        media.SetTitle();

        Assert.Equal("my-song", media.Title);
    }

    [Fact]
    public void SetTitle_HandlesPathWithMultipleDots()
    {
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, @"C:\Downloads\my.cool.song.mp3", true, "id");

        media.SetTitle();

        Assert.Equal("my.cool.song", media.Title);
    }

    [Fact]
    public void SetTitle_WindowsPath()
    {
        var media = new DownloadedMedia("url", ".mp4", DateTime.Now, @"C:\Users\Documents\video.mp4", true, "id");

        media.SetTitle();

        Assert.Equal("video", media.Title);
    }

    [Fact]
    public void SetTitle_ComplexPath()
    {
        var media = new DownloadedMedia("url", ".wav", DateTime.Now, @"C:\Music\Genre\Subfolder\audio-file.wav", true, "id");

        media.SetTitle();

        Assert.Equal("audio-file", media.Title);
    }
}

