using System.Collections.ObjectModel;
using PyScrapperDesktopApp.Models;

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
    public void SaveAndLoadMedias_RoundTrip_PreservesData()
    {
        var tempFile = Path.Combine(Path.GetTempPath(), $"test_medias_{Guid.NewGuid()}.json");

        try
        {
            var medias = new ObservableCollection<DownloadedMedia>
            {
                new("https://example.com/1", ".mp3", new DateTime(2025, 1, 1), @"C:\test\file1.mp3", true, "id1") { Id = 1 },
                new("https://example.com/2", ".mp4", new DateTime(2025, 2, 2), @"C:\test\file2.mp4", false, "id2") { Id = 2 }
            };

            DownloadedMedia.SaveMediasToJson(medias, tempFile);

            Assert.True(File.Exists(tempFile));

            var loaded = DownloadedMedia.GetMediasFromJson(tempFile);

            Assert.Equal(2, loaded.Count);
            Assert.Equal("https://example.com/1", loaded[0].Url);
            Assert.Equal(".mp3", loaded[0].MediaType);
            Assert.Equal(1, loaded[0].Id);
            Assert.True(loaded[0].IsPlayable);
            Assert.Equal("id1", loaded[0].Identifier);
            Assert.Equal("https://example.com/2", loaded[1].Url);
            Assert.Equal(".mp4", loaded[1].MediaType);
            Assert.Equal(2, loaded[1].Id);
            Assert.False(loaded[1].IsPlayable);
            Assert.Equal("id2", loaded[1].Identifier);
        }
        finally
        {
            if (File.Exists(tempFile))
                File.Delete(tempFile);
        }
    }

    [Fact]
    public void GetMediasFromJson_NonExistentFile_ReturnsEmptyCollection()
    {
        var nonExistentPath = Path.Combine(Path.GetTempPath(), "non_existent_file_12345.json");

        var result = DownloadedMedia.GetMediasFromJson(nonExistentPath);

        Assert.NotNull(result);
        Assert.Empty(result);
    }

    [Fact]
    public void SaveMediasToJson_EmptyCollection_CreatesValidJsonFile()
    {
        var tempFile = Path.Combine(Path.GetTempPath(), $"test_empty_{Guid.NewGuid()}.json");

        try
        {
            var emptyCollection = new ObservableCollection<DownloadedMedia>();
            DownloadedMedia.SaveMediasToJson(emptyCollection, tempFile);

            Assert.True(File.Exists(tempFile));

            var loaded = DownloadedMedia.GetMediasFromJson(tempFile);
            Assert.NotNull(loaded);
            Assert.Empty(loaded);
        }
        finally
        {
            if (File.Exists(tempFile))
                File.Delete(tempFile);
        }
    }

    [Fact]
    public void SaveMediasToJson_CreatesDirectoryIfNotExists()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"test_dir_{Guid.NewGuid()}");
        var tempFile = Path.Combine(tempDir, "medias.json");

        try
        {
            Assert.False(Directory.Exists(tempDir));

            var medias = new ObservableCollection<DownloadedMedia>
            {
                new("url", ".mp3", DateTime.Now, "path", true, "id") { Id = 1 }
            };

            DownloadedMedia.SaveMediasToJson(medias, tempFile);

            Assert.True(File.Exists(tempFile));
        }
        finally
        {
            if (Directory.Exists(tempDir))
                Directory.Delete(tempDir, true);
        }
    }
}

