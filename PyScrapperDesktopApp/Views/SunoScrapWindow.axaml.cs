using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class SunoScrapWindow : Window
{
    public SunoScrapWindow()
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new SunoScrapWindowViewModel(this);
        
        DataContext = vm;
        
        vm.RequestClose += Close;
    }
}