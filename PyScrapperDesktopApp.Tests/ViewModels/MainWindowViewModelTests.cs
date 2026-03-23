using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class MainWindowViewModelTests
{
    [Fact]
    public void Constructor_InitializesDownloadedMediaList()
    {
        var vm = new MainWindowViewModel();

        Assert.NotNull(vm.DownloadedMediaList);
    }
}

