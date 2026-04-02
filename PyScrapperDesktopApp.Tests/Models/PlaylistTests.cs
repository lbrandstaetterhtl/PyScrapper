using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using PyScrapperDesktopApp.Models;
using Xunit;

namespace PyScrapperDesktopApp.Tests.Models;

public class PlaylistTests
{
    /// <summary>
    /// Reset static state before each test to avoid cross-test contamination.
    /// </summary>
    public PlaylistTests()
    {
        AppData.Playlists.Clear();
        AppData.DownloadedMedias.Clear();
        AppData.PlayableMedias.Clear();
    }

    [Fact]
    public void Constructor_SetsAllPropertiesCorrectly()
    {
        var mediaIds = new List<int> { 1, 2, 3 };
        var name = "Test Playlist";
        var description = "A test playlist";

        var playlist = new Playlist(mediaIds, name, description);

        Assert.Equal(name, playlist.Name);
        Assert.Equal(description, playlist.Description);
        Assert.Equal(mediaIds, playlist.MediaIds);
        Assert.Equal(3, playlist.Count);
        Assert.Empty(playlist.PlayableMediaIds);
    }

    [Fact]
    public void SetHighestId_EmptyCollection_SetsIdTo1()
    {
        var playlist = new Playlist(new List<int>(), "Test", "Description");
        var collection = new ObservableCollection<Playlist>();

        playlist.SetHighestId(collection);

        Assert.Equal(1, playlist.Id);
    }

    [Fact]
    public void SetHighestId_CollectionWithItems_SetsIdToMaxPlusOne()
    {
        var existing1 = new Playlist(new List<int>(), "P1", "Desc1") { Id = 3 };
        var existing2 = new Playlist(new List<int>(), "P2", "Desc2") { Id = 7 };
        var existing3 = new Playlist(new List<int>(), "P3", "Desc3") { Id = 5 };

        var collection = new ObservableCollection<Playlist> { existing1, existing2, existing3 };

        var newPlaylist = new Playlist(new List<int>(), "P4", "Desc4");
        newPlaylist.SetHighestId(collection);

        Assert.Equal(8, newPlaylist.Id);
    }

    [Fact]
    public void SetPlayableMediaIds_MatchesPlayableMediasInCollection()
    {
        var playable1 = new DownloadedMedia("url1", ".mp3", DateTime.Now, "path1", true, "id1") { Id = 1 };
        var playable2 = new DownloadedMedia("url2", ".mp3", DateTime.Now, "path2", true, "id2") { Id = 2 };
        var nonPlayable = new DownloadedMedia("url3", ".mp4", DateTime.Now, "path3", false, "id3") { Id = 3 };

        var playableMedias = new ObservableCollection<DownloadedMedia> { playable1, playable2 };

        var playlist = new Playlist(new List<int> { 1, 2, 3 }, "Test", "Description");
        playlist.SetPlayableMediaIds(playableMedias);

        Assert.Equal(2, playlist.PlayableMediaIds.Count);
        Assert.Contains(1, playlist.PlayableMediaIds);
        Assert.Contains(2, playlist.PlayableMediaIds);
        Assert.DoesNotContain(3, playlist.PlayableMediaIds);
    }

    [Fact]
    public void SetPlayableMediaIds_EmptyPlayableMedias_EmptyPlayableMediaIds()
    {
        var playableMedias = new ObservableCollection<DownloadedMedia>();

        var playlist = new Playlist(new List<int> { 1, 2, 3 }, "Test", "Description");
        playlist.SetPlayableMediaIds(playableMedias);

        Assert.Empty(playlist.PlayableMediaIds);
    }

    [Fact]
    public void AddMedia_NewMediaId_AddsToMediaIds()
    {
        var playlist = new Playlist(new List<int> { 1, 2 }, "Test", "Description");
        AppData.AddPlaylist(playlist);

        playlist.AddMedia(3);

        Assert.Equal(3, playlist.MediaIds.Count);
        Assert.Contains(3, playlist.MediaIds);
        Assert.Equal(3, playlist.Count);
    }

    [Fact]
    public void AddMedia_ExistingMediaId_DoesNotAddDuplicate()
    {
        var playlist = new Playlist(new List<int> { 1, 2 }, "Test", "Description");
        AppData.AddPlaylist(playlist);

        playlist.AddMedia(2);

        Assert.Equal(2, playlist.MediaIds.Count);
        Assert.Equal(2, playlist.Count);
    }

    [Fact]
    public void RemoveMedia_ExistingMediaId_RemovesFromMediaIds()
    {
        var playlist = new Playlist(new List<int> { 1, 2, 3 }, "Test", "Description");
        AppData.AddPlaylist(playlist);

        playlist.RemoveMedia(2);

        Assert.Equal(2, playlist.MediaIds.Count);
        Assert.DoesNotContain(2, playlist.MediaIds);
        Assert.Equal(2, playlist.Count);
    }

    [Fact]
    public void RemoveMedia_NonExistentMediaId_DoesNothing()
    {
        var playlist = new Playlist(new List<int> { 1, 2, 3 }, "Test", "Description");
        AppData.AddPlaylist(playlist);

        playlist.RemoveMedia(99);

        Assert.Equal(3, playlist.MediaIds.Count);
        Assert.Equal(3, playlist.Count);
    }

    [Fact]
    public void AddPlaylist_AddsToCollection()
    {
        var playlist = new Playlist(new List<int> { 1 }, "Test", "Description");

        AppData.AddPlaylist(playlist);

        Assert.Single(AppData.Playlists);
        Assert.Contains(playlist, AppData.Playlists);
    }

    [Fact]
    public void RemovePlaylist_RemovesFromCollection()
    {
        var playlist = new Playlist(new List<int> { 1 }, "Test", "Description");
        AppData.AddPlaylist(playlist);

        AppData.RemovePlaylist(playlist);

        Assert.Empty(AppData.Playlists);
    }

    [Fact]
    public void MultipleAddMedia_SequentialUpdates()
    {
        var playlist = new Playlist(new List<int> { 1 }, "Test", "Description");
        AppData.AddPlaylist(playlist);

        playlist.AddMedia(2);
        playlist.AddMedia(3);
        playlist.AddMedia(4);

        Assert.Equal(4, playlist.Count);
        Assert.Contains(1, playlist.MediaIds);
        Assert.Contains(2, playlist.MediaIds);
        Assert.Contains(3, playlist.MediaIds);
        Assert.Contains(4, playlist.MediaIds);
    }
}

