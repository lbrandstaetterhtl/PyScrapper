using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class GetServerHealthWindow : Window
{
    public GetServerHealthWindow()
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new GetServerHealthWindowViewModel(new DialogService(this));
        DataContext = vm;
        
        vm.CloseRequested += Close;
        
        Opened += (_, _) => vm.StartHealthCheck();
        
        Closed += (_, _) => vm.StopHealthCheck();
    }
}