using Avalonia.Controls;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class InputWindow : Window
{
    public InputWindow(string massage)
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new InputWindowViewModel(this, massage);
        DataContext = vm;
    }
}