using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class GetServerHealthWindow : Window
{
    public GetServerHealthWindow()
    {
        InitializeComponent();
        
        var vm = new GetServerHealthWindowViewModel();
        DataContext = vm;
        
        vm.CloseRequested += Close;
        
        Opened += (_, _) => vm.StartHealthCheck();
        
        Closed += (_, _) => vm.StopHealthCheck();
    }
}