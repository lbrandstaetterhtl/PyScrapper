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
        TitleBar.Initialize(this);
        
        DialogService ds = new(this);

       var vm = new ScrapWindowWithSearchViewModel(this, provider, ds);

        DataContext = vm;

        vm.RequestClose += Close;

        int buttonCount = 0;

        EnterButton.Click += async (sender, args) =>
        {
            if (buttonCount == 0)
            {
                SearchGrid.IsVisible = false;
                ResultsGrid.IsVisible = true;
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
                buttonCount--;
            }
        };

        if (provider == "bandcamp" || provider == "bandcamp.com")
        {
            MediaTypePanel.IsVisible = false;
        }
    }
}