using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class ScrapWindowWithoutSearch : Window
{
    public ScrapWindowWithoutSearch()
    {
        if (Design.IsDesignMode) return;

        InitializeComponent();
        TitleBar.Initialize(this);
        
        DialogService ds = new DialogService(this);
        
        var vm = new ScrapWindowWithoutSearchViewModel(ds);
        
        DataContext = vm;
        
        vm.RequestClose += Close;
    }
}