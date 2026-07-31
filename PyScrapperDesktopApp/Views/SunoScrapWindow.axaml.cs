using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class SunoScrapWindow : Window
{
    public SunoScrapWindow()
    {
        if (Design.IsDesignMode) return;

        InitializeComponent();
        TitleBar.Initialize(this);
        
        DialogService ds = new DialogService(this);
        
        var vm = new SunoScrapWindowViewModel(ds);
        
        DataContext = vm;
        
        vm.RequestClose += Close;
    }
}