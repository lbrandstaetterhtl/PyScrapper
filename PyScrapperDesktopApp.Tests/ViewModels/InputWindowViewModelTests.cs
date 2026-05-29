using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

[Collection("Avalonia")]
public class InputWindowViewModelTests
{
    [Fact]
    public void OkCommand_Exists()
    {
        var vm = new InputWindowViewModel(new Window(), "Message");
        Assert.NotNull(vm.OkCommand);
    }

    [Fact]
    public void CancelCommand_Exists()
    {
        var vm = new InputWindowViewModel(new Window(), "Message");
        Assert.NotNull(vm.CancelCommand);
    }

    [Fact]
    public void Properties_SetCorrectly()
    {
        var message = "Input Message";
        var vm = new InputWindowViewModel(new Window(), message);

        Assert.Equal(message, vm.Massage);
        Assert.Null(vm.InputText);
    }
}
