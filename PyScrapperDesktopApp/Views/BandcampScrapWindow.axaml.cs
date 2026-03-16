using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class BandcampScrapWindow : Window
{
    public BandcampScrapWindow()
    {
        InitializeComponent();
        
        var vm = new ViewModels.BandcampScrapWindowViewModel(this);
        
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
    }
}