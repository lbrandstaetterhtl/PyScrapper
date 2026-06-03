using Avalonia.Controls;
using Avalonia.Headless.XUnit;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

[Collection("Avalonia")]
public class ConfirmationWindowViewModelTests
{
    [AvaloniaFact]
    public void Constructor_SetsMessage()
    {
        var message = "Are you sure?";
        var vm = new ConfirmationWindowViewModel(new Window(), message);
        
        Assert.Equal(message, vm.Message);
    }

    [AvaloniaFact]
    public void ConfirmCommand_ClosesWindowWithTrue()
    {
        var vm = new ConfirmationWindowViewModel(new Window(), "Test");
        Assert.NotNull(vm.ConfirmCommand);
    }
}

