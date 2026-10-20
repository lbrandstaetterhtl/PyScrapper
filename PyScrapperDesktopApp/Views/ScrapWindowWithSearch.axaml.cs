using System.Threading;
using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class ScrapWindowWithSearch : Window
{
    public ScrapWindowWithSearch(string provider)
    {
        if (Design.IsDesignMode) return;

        InitializeComponent();
        
        DialogService ds = new(this);

        CancellationTokenSource cts = new();
       var vm = new ScrapWindowWithSearchViewModel(this, provider, ds, out cts);
       
       TitleBar.Initialize(this, cts, vm.CancelDownload);

        DataContext = vm;

        vm.RequestClose += Close;

        int buttonCount = 0;

        EnterButton.Click += async (sender, args) =>
        {
            if (buttonCount == 0)
            {
                SearchGrid.IsVisible = false;
                ResultsGrid.IsVisible = true;
                ResultsScrollViewer.IsVisible = true;
                await vm.Search();
                buttonCount++;
            }
        };

        BackToSearch.Click += (sender, args) =>
        {
            if (buttonCount == 1)
            {
                SearchGrid.IsVisible = true;
                ResultsGrid.IsVisible = false;
                ResultsScrollViewer.IsVisible = false;
                buttonCount--;
            }
        };
    }
}