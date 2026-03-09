using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class ViewModelBaseTests
{
    private class TestViewModel : ViewModelBase
    {
        private string? _testProperty;
        
        public string? TestProperty
        {
            get => _testProperty;
            set => SetProperty(ref _testProperty, value);
        }
    }

    [Fact]
    public void ViewModelBase_InheritsObservableObject()
    {
        var vm = new TestViewModel();

        Assert.IsAssignableFrom<CommunityToolkit.Mvvm.ComponentModel.ObservableObject>(vm);
    }

    [Fact]
    public void SetProperty_RaisesPropertyChanged()
    {
        var vm = new TestViewModel();
        var raised = false;

        vm.PropertyChanged += (_, args) =>
        {
            if (args.PropertyName == nameof(TestViewModel.TestProperty))
                raised = true;
        };

        vm.TestProperty = "Hello";

        Assert.True(raised);
        Assert.Equal("Hello", vm.TestProperty);
    }

    [Fact]
    public void SetProperty_SameValue_DoesNotRaisePropertyChanged()
    {
        var vm = new TestViewModel();
        vm.TestProperty = "Same";

        var raised = false;
        vm.PropertyChanged += (_, _) => raised = true;

        vm.TestProperty = "Same";

        Assert.False(raised);
    }
}

