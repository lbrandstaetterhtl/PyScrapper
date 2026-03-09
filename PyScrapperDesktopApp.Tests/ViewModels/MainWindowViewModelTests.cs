using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class MainWindowViewModelTests
{
    [Fact]
    public void Constructor_InitializesDownloadedMediaList()
    {
        var vm = new MainWindowViewModel();

        Assert.NotNull(vm.DownloadedMediaList);
    }

    [Fact]
    public void HealthCheckResult_SetGet_Works()
    {
        var vm = new MainWindowViewModel();

        vm.HealthCheckResult = "Server is healthy";

        Assert.Equal("Server is healthy", vm.HealthCheckResult);
    }

    [Fact]
    public void HealthCheckResult_RaisesPropertyChanged()
    {
        var vm = new MainWindowViewModel();
        var propertyChangedRaised = false;
        string? changedPropertyName = null;

        vm.PropertyChanged += (sender, args) =>
        {
            propertyChangedRaised = true;
            changedPropertyName = args.PropertyName;
        };

        vm.HealthCheckResult = "test";

        Assert.True(propertyChangedRaised);
        Assert.Equal(nameof(vm.HealthCheckResult), changedPropertyName);
    }

    [Fact]
    public void DownloadedMediaList_SetGet_Works()
    {
        var vm = new MainWindowViewModel();
        var newList = new System.Collections.ObjectModel.ObservableCollection<PyScrapperDesktopApp.Models.DownloadedMedia>();

        vm.DownloadedMediaList = newList;

        Assert.Same(newList, vm.DownloadedMediaList);
    }

    [Fact]
    public void DownloadedMediaList_RaisesPropertyChanged()
    {
        var vm = new MainWindowViewModel();
        var propertyChangedRaised = false;
        string? changedPropertyName = null;

        vm.PropertyChanged += (sender, args) =>
        {
            propertyChangedRaised = true;
            changedPropertyName = args.PropertyName;
        };

        vm.DownloadedMediaList = new System.Collections.ObjectModel.ObservableCollection<PyScrapperDesktopApp.Models.DownloadedMedia>();

        Assert.True(propertyChangedRaised);
        Assert.Equal(nameof(vm.DownloadedMediaList), changedPropertyName);
    }

    [Fact]
    public void HealthCheckResult_InitiallyNull()
    {
        var vm = new MainWindowViewModel();

        Assert.Null(vm.HealthCheckResult);
    }
}

