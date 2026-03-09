using System.Linq;
using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

[Collection("Avalonia")]
public class SunoScrapWindowViewModelTests
{
    private SunoScrapWindowViewModel CreateVm()
    {
        var window = new Window();
        return new SunoScrapWindowViewModel(window);
    }

    [Fact]
    public void SunoUrl_SetGet_Works()
    {
        var vm = CreateVm();
        vm.SunoUrl = "https://suno.com/song/123";
        Assert.Equal("https://suno.com/song/123", vm.SunoUrl);
    }

    [Fact]
    public void SunoUrl_RaisesPropertyChanged()
    {
        var vm = CreateVm();
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(SunoScrapWindowViewModel.SunoUrl))
                raised = true;
        };
        vm.SunoUrl = "https://suno.com/song/456";
        Assert.True(raised);
    }

    [Fact]
    public void SelectedMediaType_SetGet_Works()
    {
        var vm = CreateVm();
        vm.SelectedMediaType = ".mp3";
        Assert.Equal(".mp3", vm.SelectedMediaType);
    }

    [Fact]
    public void SelectedMediaType_RaisesPropertyChanged()
    {
        var vm = CreateVm();
        var raised = false;
        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(SunoScrapWindowViewModel.SelectedMediaType))
                raised = true;
        };
        vm.SelectedMediaType = ".mp4";
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
    public void ScrapCommand_IsNotNull()
    {
        var vm = CreateVm();
        Assert.NotNull(vm.ScrapCommand);
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
    public void SunoUrl_InitiallyNull()
    {
        var vm = CreateVm();
        Assert.Null(vm.SunoUrl);
    }

    [Fact]
    public void SelectedMediaType_InitiallyNull()
    {
        var vm = CreateVm();
        Assert.Null(vm.SelectedMediaType);
    }
}
