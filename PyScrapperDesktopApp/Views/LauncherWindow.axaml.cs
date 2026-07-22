using Avalonia.Controls;
using Avalonia.Threading;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public enum LauncherResult
{
    Cancelled,
    Success,
    Error
}

public partial class LauncherWindow : Window
{
    private LauncherWindowViewModel _vm;

    public LauncherResult Result { get; set; } = LauncherResult.Cancelled;
    
    public LauncherWindow()
    {
        if (Design.IsDesignMode) return;

        InitializeComponent();

        _vm = new LauncherWindowViewModel(new DialogService(this));
        DataContext = _vm;

        Opened += (s, e) =>
        {
            _vm.OnWindowReady(this);
            TitleBar.Initialize(this);
        };

        _vm.Messages.CollectionChanged += (s, e) =>
        {
            Dispatcher.UIThread.Post(() =>
            {
                MessagesScrollViewer.ScrollToEnd();
            }, DispatcherPriority.Loaded);
        };
    }
}
