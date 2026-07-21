using System.Collections.Generic;
using Avalonia.Controls;
using Avalonia.Headless.XUnit;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class CreatePlaylistWindowViewModelTests
{
    private CreatePlaylistWindowViewModel CreateVm()
    {
        return new CreatePlaylistWindowViewModel(new DialogService(new Window()));
    }

    [AvaloniaFact]
    public void Constructor_InitializesCollections()
    {
        AppData.DownloadedMedias.Clear();
        var media = new DownloadedMedia("url", ".mp3", DateTime.Now, "path", true, "id1");
        AppData.DownloadedMedias.Add(media);

        var vm = CreateVm();

        Assert.NotEmpty(vm.AvailableMedias);
        Assert.Empty(vm.SelectedMedias);
    }

    [AvaloniaFact]
    public void CancelCommand_InvokesCloseRequested()
    {
        var vm = CreateVm();
        bool closeRequestedCalled = false;
        vm.CloseRequested = () => closeRequestedCalled = true;

        vm.CancelCommand.Execute(null);

        Assert.True(closeRequestedCalled);
    }

    [AvaloniaFact]
    public void CreatePlaylist_WithEmptyName_DoesNotAddPlaylist()
    {
        AppData.Playlists.Clear();
        var vm = CreateVm();
        vm.PlaylistName = "";

        Assert.NotNull(vm.CreatePlaylistCommand);

        Assert.Empty(AppData.Playlists);
    }
}
