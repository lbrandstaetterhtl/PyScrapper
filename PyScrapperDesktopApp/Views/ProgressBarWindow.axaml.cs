using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class ProgressBarWindow : Window
{
    public ProgressBarWindow()
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new ViewModels.ProgressBarWindowViewModel();
        vm.CloseRequested += Close;
        DataContext = vm;
    }
}