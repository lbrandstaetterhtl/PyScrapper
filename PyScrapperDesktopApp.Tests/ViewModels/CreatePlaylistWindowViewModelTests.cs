using System.Collections.Generic;
using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

[Collection("Avalonia")]
public class CreatePlaylistWindowViewModelTests
{
    private CreatePlaylistWindowViewModel CreateVm()
    {
        return new CreatePlaylistWindowViewModel(new Window());
    }

    [Fact]
    public void Constructor_InitializesCollections()
    {
        AppData.DownloadedMedias.Clear();
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id1");
        AppData.DownloadedMedias.Add(media);

        var vm = CreateVm();

        Assert.NotEmpty(vm.AvailableMedias);
        Assert.Empty(vm.SelectedMedias);
    }

    [Fact]
    public void CancelCommand_InvokesCloseRequested()
    {
        var vm = CreateVm();
        bool closeRequestedCalled = false;
        vm.CloseRequested = () => closeRequestedCalled = true;

        vm.CancelCommand.Execute(null);

        Assert.True(closeRequestedCalled);
    }

    [Fact]
    public void CreatePlaylist_WithEmptyName_DoesNotAddPlaylist()
    {
        AppData.Playlists.Clear();
        var vm = CreateVm();
        vm.PlaylistName = "";

        // This will attempt to show a MessageBox, which might be tricky in headless,
        // but we can check if a playlist was added.
        vm.CreatePlaylistCommand.Execute(null);

        Assert.Empty(AppData.Playlists);
    }
}
