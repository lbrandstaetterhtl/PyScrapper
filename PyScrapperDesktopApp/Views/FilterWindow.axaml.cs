using Avalonia.Controls;
using Avalonia.Controls.Chrome;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class FilterWindow : Window
{
    public FilterWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);

        var vm = new FilterWindowViewModel();
        DataContext = vm;
        
        vm.CloseRequested += Close;
    }
}