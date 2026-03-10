using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class ProgressBarWindow : Window
{
    public ProgressBarWindow()
    {
        InitializeComponent();
        
        var vm = new ViewModels.ProgressBarWindowViewModel();
        vm.CloseRequested += Close;
        DataContext = vm;
    }
}