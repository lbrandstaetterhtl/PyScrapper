using System.Threading;
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
        
        DialogService ds = new DialogService(this);
        
        CancellationTokenSource cts = new CancellationTokenSource();
        var vm = new ScrapWindowWithoutSearchViewModel(ds, this, out cts);
        TitleBar.Initialize(this, cts, vm.CancelDownload);
        
        DataContext = vm;
        
        vm.RequestClose += Close;
    }
}