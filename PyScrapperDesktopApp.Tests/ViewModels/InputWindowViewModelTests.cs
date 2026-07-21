using Avalonia.Controls;
using Avalonia.Headless.XUnit;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class InputWindowViewModelTests
{
    [AvaloniaFact]
    public void OkCommand_Exists()
    {
        var vm = new InputWindowViewModel(new Window(), "Message");
        Assert.NotNull(vm.OkCommand);
    }

    [AvaloniaFact]
    public void CancelCommand_Exists()
    {
        var vm = new InputWindowViewModel(new Window(), "Message");
        Assert.NotNull(vm.CancelCommand);
    }

    [AvaloniaFact]
    public void Properties_SetCorrectly()
    {
        var message = "Input Message";
        var vm = new InputWindowViewModel(new Window(), message);

        Assert.Equal(message, vm.Massage);
        Assert.Null(vm.InputText);
    }
}
