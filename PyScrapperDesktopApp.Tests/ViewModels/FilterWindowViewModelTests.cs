using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class FilterWindowViewModelTests
{
    [Fact]
    public void InitialValues_AreCorrect()
    {
        var vm = new FilterWindowViewModel();
        Assert.Null(vm.SearchQuery);
        Assert.Empty(vm.SelectedMediaTypes);
        Assert.Null(vm.StartDate);
        Assert.Null(vm.EndDate);
        Assert.False(vm.IsPlayable);
    }

    [Fact]
    public void CancelCommand_InvokesCloseRequested()
    {
        var vm = new FilterWindowViewModel();
        bool closeRequestedCalled = false;
        vm.CloseRequested = () => closeRequestedCalled = true;

        vm.CancelCommand.Execute(null);

        Assert.True(closeRequestedCalled);
    }

    [Fact]
    public void SelectedMediaTypes_CanBeModified()
    {
        var vm = new FilterWindowViewModel();
        vm.SelectedMediaTypes.Add(".mp3");
        
        Assert.Single(vm.SelectedMediaTypes);
        Assert.Equal(".mp3", vm.SelectedMediaTypes[0]);
    }
}

