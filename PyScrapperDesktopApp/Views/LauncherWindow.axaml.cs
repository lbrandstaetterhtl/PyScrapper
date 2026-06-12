using Avalonia.Controls;
using Avalonia.Threading;
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

        _vm = new LauncherWindowViewModel();
        DataContext = _vm;

        Opened += (s, e) =>
        {
            _vm.OnWindowReady(this);
            TitleBar.Initialize(this);
        };

        _vm.Messages.CollectionChanged += (s, e) =>
        {
            // Nach dem Layout-Pass ans Ende scrollen
            Dispatcher.UIThread.Post(() =>
            {
                MessagesScrollViewer.ScrollToEnd();
            }, DispatcherPriority.Loaded);
        };
    }
}
