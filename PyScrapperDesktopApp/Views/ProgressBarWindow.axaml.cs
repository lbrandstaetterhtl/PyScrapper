using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class ProgressBarWindow : Window
{
    public ProgressBarWindow(string id)
    {
        InitializeComponent();
        
        var vm = new ViewModels.ProgressBarWindowViewModel(id);
        vm.CloseRequested += Close;
        DataContext = vm;
    }
}