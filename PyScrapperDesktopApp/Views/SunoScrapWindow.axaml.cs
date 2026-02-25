using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class SunoScrapWindow : Window
{
    public SunoScrapWindow()
    {
        InitializeComponent();
        
        var vm = new SunoScrapWindowViewModel();
        
        DataContext = vm;
        
        vm.RequestClose += Close;
    }
}