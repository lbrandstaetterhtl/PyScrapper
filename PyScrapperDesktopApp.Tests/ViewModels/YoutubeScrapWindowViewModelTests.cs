using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;
using static PyScrapperDesktopApp.Models.ApiClient;

namespace PyScrapperDesktopApp.Tests.ViewModels;

[Collection("Avalonia")]
public class YoutubeScrapWindowViewModelTests
{
    private YoutubeScrapWindowViewModel CreateVm()
    {
        var window = new Window();
        return new YoutubeScrapWindowViewModel(window);
    }

    [Fact]
    public void SearchQuery_SetGet_Works()
    {
        var vm = CreateVm();
        vm.SearchQuery = "test search";
        Assert.Equal("test search", vm.SearchQuery);
    }

    [Fact]
    public void SearchQuery_RaisesPropertyChanged()
    {
        var vm = CreateVm();
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(YoutubeScrapWindowViewModel.SearchQuery))
                raised = true;
        };
        vm.SearchQuery = "changed";
        Assert.True(raised);
    }

    [Fact]
    public void SearchQuery_SameValue_DoesNotRaisePropertyChanged()
    {
        var vm = CreateVm();
        vm.SearchQuery = "same";
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(YoutubeScrapWindowViewModel.SearchQuery))
                raised = true;
        };
        vm.SearchQuery = "same";
        Assert.False(raised);
    }

    [Fact]
    public void SearchResultsCount_SetGet_Works()
    {
        var vm = CreateVm();
        vm.SearchResultsCount = "10";
        Assert.Equal("10", vm.SearchResultsCount);
    }

    [Fact]
    public void SearchResultsCount_RaisesPropertyChanged()
    {
        var vm = CreateVm();
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(YoutubeScrapWindowViewModel.SearchResultsCount))
                raised = true;
        };
        vm.SearchResultsCount = "5";
        Assert.True(raised);
    }

    [Fact]
    public void YoutubeVideoItems_SetGet_Works()
    {
        var vm = CreateVm();
        var items = new List<YoutubeVideoItem>
        {
            new() { videoId = "abc", title = "Test" }
        };
        vm.YoutubeVideoItems = items;
        Assert.Single(vm.YoutubeVideoItems);
        Assert.Equal("abc", vm.YoutubeVideoItems[0].videoId);
    }

    [Fact]
    public void YoutubeVideoItems_RaisesPropertyChanged()
    {
        var vm = CreateVm();
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(YoutubeScrapWindowViewModel.YoutubeVideoItems))
                raised = true;
        };
        vm.YoutubeVideoItems = new List<YoutubeVideoItem>();
        Assert.True(raised);
    }

    [Fact]
    public void SelectedYoutubeVideoItems_SetGet_Works()
    {
        var vm = CreateVm();
        var items = new List<YoutubeVideoItem>
        {
            new() { videoId = "sel1", title = "Selected" }
        };
        vm.SelectedYoutubeVideoItems = items;
        Assert.Single(vm.SelectedYoutubeVideoItems);
    }

    [Fact]
    public void SelectedMediaType_SetGet_Works()
    {
        var vm = CreateVm();
        vm.SelectedMediaType = ".mp4";
        Assert.Equal(".mp4", vm.SelectedMediaType);
    }

    [Fact]
    public void SelectedMediaType_RaisesPropertyChanged()
    {
        var vm = CreateVm();
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(YoutubeScrapWindowViewModel.SelectedMediaType))
                raised = true;
        };
        vm.SelectedMediaType = ".mp3";
        Assert.True(raised);
    }

    [Fact]
    public void AvailableMediaTypes_ContainsMp3AndMp4()
    {
        var vm = CreateVm();
        var types = vm.AvailableMediaTypes.ToList();
        Assert.Contains(".mp3", types);
        Assert.Contains(".mp4", types);
        Assert.Equal(2, types.Count);
    }

    [Fact]
    public void CancelCommand_IsNotNull()
    {
        var vm = CreateVm();
        Assert.NotNull(vm.CancelCommand);
    }

    [Fact]
    public void CancelCommand_InvokesRequestClose()
    {
        var vm = CreateVm();
        var closeCalled = false;
        vm.RequestClose += () => closeCalled = true;
        vm.CancelCommand.Execute(null);
        Assert.True(closeCalled);
    }

    [Fact]
    public void YoutubeVideoItems_InitiallyEmpty()
    {
        var vm = CreateVm();
        Assert.NotNull(vm.YoutubeVideoItems);
        Assert.Empty(vm.YoutubeVideoItems);
    }

    [Fact]
    public void SelectedYoutubeVideoItems_InitiallyEmpty()
    {
        var vm = CreateVm();
        Assert.NotNull(vm.SelectedYoutubeVideoItems);
        Assert.Empty(vm.SelectedYoutubeVideoItems);
    }

    [Fact]
    public void SearchQuery_InitiallyNull()
    {
        var vm = CreateVm();
        Assert.Null(vm.SearchQuery);
    }

    [Fact]
    public void SelectedMediaType_InitiallyNull()
    {
        var vm = CreateVm();
        Assert.Null(vm.SelectedMediaType);
    }
}
