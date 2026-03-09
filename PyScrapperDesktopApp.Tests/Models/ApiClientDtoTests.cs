using System.Text.Json;
using PyScrapperDesktopApp.Models;
using static PyScrapperDesktopApp.Models.ApiClient;

namespace PyScrapperDesktopApp.Tests.Models;

public class ApiClientDtoTests
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    #region DownloadRequestData Tests

    [Fact]
    public void DownloadRequestData_Serialization_UsesJsonPropertyNames()
    {
        var request = new DownloadRequestData
        {
            Provider = "youtube",
            Url = "https://youtube.com/watch?v=abc",
            Mediatype = ".mp3",
            Download_path = @"C:\Downloads"
        };

        var json = JsonSerializer.Serialize(request, JsonOptions);

        Assert.Contains("\"provider\"", json);
        Assert.Contains("\"url\"", json);
        Assert.Contains("\"mediatype\"", json);
        Assert.Contains("\"download_path\"", json);
        Assert.Contains("youtube", json);
    }

    [Fact]
    public void DownloadRequestData_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "provider": "suno",
            "url": "https://suno.com/song/123",
            "mediatype": ".mp4",
            "download_path": "/tmp/downloads"
        }
        """;

        var data = JsonSerializer.Deserialize<DownloadRequestData>(json, JsonOptions);

        Assert.NotNull(data);
        Assert.Equal("suno", data.Provider);
        Assert.Equal("https://suno.com/song/123", data.Url);
        Assert.Equal(".mp4", data.Mediatype);
        Assert.Equal("/tmp/downloads", data.Download_path);
    }

    #endregion

    #region DownloadSuccessResponse Tests

    [Fact]
    public void DownloadSuccessResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "job-1",
            "jobtype": "download",
            "status": "complete",
            "message": {
                "Provider": "youtube",
                "identifier": "XPwUIDYKHX4",
                "File": "C:\\Downloads\\test.mp3",
                "Raw_status": "Download complete"
            }
        }
        """;

        var response = JsonSerializer.Deserialize<DownloadSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("job-1", response.Id);
        Assert.Equal("download", response.JobType);
        Assert.Equal("complete", response.Status);
        Assert.NotNull(response.Message);
        Assert.Equal("youtube", response.Message.Provider);
        Assert.Equal("XPwUIDYKHX4", response.Message.identifier);
        Assert.Equal("C:\\Downloads\\test.mp3", response.Message.File);
        Assert.Equal("Download complete", response.Message.Raw_status);
    }

    #endregion

    #region DownloadErrorResponse Tests

    [Fact]
    public void DownloadErrorResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "job-2",
            "jobtype": "download",
            "status": "error",
            "message": {
                "Error": "Video not found",
                "Url": "https://youtube.com/invalid"
            }
        }
        """;

        var response = JsonSerializer.Deserialize<DownloadErrorResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("job-2", response.Id);
        Assert.Equal("error", response.Status);
        Assert.NotNull(response.Message);
        Assert.Equal("Video not found", response.Message.Error);
        Assert.Equal("https://youtube.com/invalid", response.Message.Url);
    }

    #endregion

    #region HealthResponse Tests

    [Fact]
    public void HealthResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "ok": true,
            "uptime_seconds": 3600.5,
            "memory_mb": 256.3,
            "pid": 12345,
            "processes": [
                {"Pid": 111, "Name": "ffmpeg"},
                {"Pid": 222, "Name": "yt-dlp"}
            ]
        }
        """;

        var response = JsonSerializer.Deserialize<HealthResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.True(response.Ok);
        Assert.Equal(3600.5, response.UptimeSeconds);
        Assert.Equal(256.3, response.MemoryMb);
        Assert.Equal(12345, response.Pid);
        Assert.NotNull(response.Processes);
        Assert.Equal(2, response.Processes.Count);
        Assert.Equal("ffmpeg", response.Processes[0].Name);
        Assert.Equal(111, response.Processes[0].Pid);
    }

    [Fact]
    public void HealthResponse_EmptyProcesses_DeserializesCorrectly()
    {
        var json = """
        {
            "ok": true,
            "uptime_seconds": 10.0,
            "memory_mb": 50.0,
            "pid": 1,
            "processes": []
        }
        """;

        var response = JsonSerializer.Deserialize<HealthResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Empty(response.Processes);
    }

    #endregion

    #region HealthErrorResponse Tests

    [Fact]
    public void HealthErrorResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "msg": "Server is unavailable",
            "type": "ERROR"
        }
        """;

        var response = JsonSerializer.Deserialize<HealthErrorResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("Server is unavailable", response.msg);
        Assert.Equal("ERROR", response.type);
    }

    #endregion

    #region SearchRequestData Tests

    [Fact]
    public void SearchRequestData_Serialization_UsesJsonPropertyNames()
    {
        var request = new SearchRequestData
        {
            Provider = "youtube",
            Search = "funny cats",
            Top = 5
        };

        var json = JsonSerializer.Serialize(request, JsonOptions);

        Assert.Contains("\"provider\"", json);
        Assert.Contains("\"search\"", json);
        Assert.Contains("\"top\"", json);
        Assert.Contains("youtube", json);
        Assert.Contains("funny cats", json);
    }

    [Fact]
    public void SearchRequestData_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "provider": "youtube",
            "search": "music video",
            "top": 10
        }
        """;

        var data = JsonSerializer.Deserialize<SearchRequestData>(json, JsonOptions);

        Assert.NotNull(data);
        Assert.Equal("youtube", data.Provider);
        Assert.Equal("music video", data.Search);
        Assert.Equal(10, data.Top);
    }

    #endregion

    #region SearchSuccessResponse Tests

    [Fact]
    public void SearchSuccessResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "search-1",
            "jobtype": "search",
            "status": "ok",
            "message": {
                "provider": "youtube",
                "query": "test query",
                "results": [
                    {
                        "videoId": "abc123",
                        "url": "https://youtube.com/watch?v=abc123",
                        "thumbnail": "https://img.youtube.com/vi/abc123/0.jpg",
                        "title": "Test Video"
                    }
                ]
            }
        }
        """;

        var response = JsonSerializer.Deserialize<SearchSuccessResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("search-1", response.VideoId);
        Assert.Equal("search", response.Jobtype);
        Assert.Equal("ok", response.Status);
        Assert.NotNull(response.Message);
        Assert.Equal("youtube", response.Message.provider);
        Assert.Equal("test query", response.Message.query);
        Assert.Single(response.Message.results);
        Assert.Equal("abc123", response.Message.results[0].videoId);
        Assert.Equal("Test Video", response.Message.results[0].title);
    }

    #endregion

    #region SearchErrorResponse Tests

    [Fact]
    public void SearchErrorResponse_Deserialization_WorksCorrectly()
    {
        var json = """
        {
            "id": "search-err-1",
            "jobtype": "search",
            "status": "error",
            "message": {
                "Error": "Search failed",
                "Query": "broken query"
            }
        }
        """;

        var response = JsonSerializer.Deserialize<SearchErrorResponse>(json, JsonOptions);

        Assert.NotNull(response);
        Assert.Equal("search-err-1", response.Id);
        Assert.Equal("error", response.Status);
        Assert.NotNull(response.Message);
        Assert.Equal("Search failed", response.Message.Error);
        Assert.Equal("broken query", response.Message.Query);
    }

    #endregion

    #region YoutubeVideoItem Tests

    [Fact]
    public void YoutubeVideoItem_Properties_CanBeSetAndRead()
    {
        var item = new YoutubeVideoItem
        {
            videoId = "XPwUIDYKHX4",
            url = "https://youtube.com/watch?v=XPwUIDYKHX4",
            thumbnail = "https://img.youtube.com/vi/XPwUIDYKHX4/0.jpg",
            title = "Test Video Title"
        };

        Assert.Equal("XPwUIDYKHX4", item.videoId);
        Assert.Equal("https://youtube.com/watch?v=XPwUIDYKHX4", item.url);
        Assert.Equal("https://img.youtube.com/vi/XPwUIDYKHX4/0.jpg", item.thumbnail);
        Assert.Equal("Test Video Title", item.title);
        Assert.Null(item.ThumbnailBitmap); // Not set from JSON
    }

    #endregion

    #region ServerProcess Tests

    [Fact]
    public void ServerProcess_Properties_CanBeSetAndRead()
    {
        var process = new ServerProcess
        {
            Pid = 12345,
            Name = "ffmpeg"
        };

        Assert.Equal(12345, process.Pid);
        Assert.Equal("ffmpeg", process.Name);
    }

    #endregion

    #region Roundtrip Serialization Tests

    [Fact]
    public void DownloadRequestData_RoundTrip_PreservesData()
    {
        var original = new DownloadRequestData
        {
            Provider = "youtube",
            Url = "https://youtube.com/watch?v=abc",
            Mediatype = ".mp3",
            Download_path = @"C:\Downloads"
        };

        var json = JsonSerializer.Serialize(original, JsonOptions);
        var deserialized = JsonSerializer.Deserialize<DownloadRequestData>(json, JsonOptions);

        Assert.NotNull(deserialized);
        Assert.Equal(original.Provider, deserialized.Provider);
        Assert.Equal(original.Url, deserialized.Url);
        Assert.Equal(original.Mediatype, deserialized.Mediatype);
        Assert.Equal(original.Download_path, deserialized.Download_path);
    }

    [Fact]
    public void SearchRequestData_RoundTrip_PreservesData()
    {
        var original = new SearchRequestData
        {
            Provider = "youtube",
            Search = "test search",
            Top = 15
        };

        var json = JsonSerializer.Serialize(original, JsonOptions);
        var deserialized = JsonSerializer.Deserialize<SearchRequestData>(json, JsonOptions);

        Assert.NotNull(deserialized);
        Assert.Equal(original.Provider, deserialized.Provider);
        Assert.Equal(original.Search, deserialized.Search);
        Assert.Equal(original.Top, deserialized.Top);
    }

    #endregion
}

