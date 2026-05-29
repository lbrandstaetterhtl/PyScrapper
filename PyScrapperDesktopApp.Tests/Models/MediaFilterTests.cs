using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.Tests.Models;

public class MediaFilterTests
{
    [Fact]
    public void BuildMediaFilter_SetsPropertiesCorrectly()
    {
        var query = "test";
        var types = new ObservableCollection<string> { ".mp3" };
        var start = DateTimeOffset.Now.AddDays(-1);
        var end = DateTimeOffset.Now;
        var playable = true;

        var filter = MediaFilter.BuildMediaFilter(query, types, start, end, playable);

        Assert.Equal(query, filter.SearchQuery);
        Assert.Equal(types, filter.MediaTypes);
        Assert.Equal(start, filter.StartDate);
        Assert.Equal(end, filter.EndDate);
        Assert.Equal(playable, filter.IsPlayable);
    }

    [Fact]
    public async Task ApplyAndClearFilter_WorksCorrectly()
    {
        // Setup
        AppData.DownloadedMedias.Clear();
        AppData.OriginalDownloadedMedias.Clear();
        AppData.FilterEnabled = false;

        var media1 = new DownloadedMedia("url1", ".mp3", DateTime.Now, "path1.mp3", true, "id1") { Id = 1, Title = "Song A" };
        var media2 = new DownloadedMedia("url2", ".mp4", DateTime.Now, "path2.mp4", true, "id2") { Id = 2, Title = "Video B" };
        
        AppData.AddDownloadedMedia(media1);
        AppData.AddDownloadedMedia(media2);

        var filter = MediaFilter.BuildMediaFilter("Song", null, null, null, false);

        // Apply
        // Note: ApplyMediaFilter has a dependency on App.Current for the MessageBox on error, 
        // but if it succeeds, it shouldn't hit that code path.
        await MediaFilter.ApplyMediaFilter(filter);

        Assert.True(AppData.FilterEnabled);
        Assert.Single(AppData.DownloadedMedias);
        Assert.Equal("Song A", AppData.DownloadedMedias[0].Title);

        // Clear
        await MediaFilter.ClearFilter();

        Assert.False(AppData.FilterEnabled);
        Assert.Equal(2, AppData.DownloadedMedias.Count);
    }
}
