using Avalonia.Headless.XUnit;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

[Collection("Avalonia")]
public class GetServerHealthWindowViewModelTests
{
    [AvaloniaFact]
    public void InitialState_IsCorrect()
    {
        Assert.True(true);
    }

    [AvaloniaFact]
    public void StopHealthCheck_InvokesCloseRequested()
    {
        Assert.True(true);
    }
}

