using System.IO;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Media.Imaging;
using CommunityToolkit.Mvvm.ComponentModel;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.Views.Controls;

public partial class TitleBarControl : UserControl
{
    private Window? _window;

    private  Bitmap closeIcon => AppData.Settings.DarkModeEnabled
        ? new Bitmap(Path.Combine(AppData.AssetPath, "DarkMode", "close-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "LightMode", "close-lightmode.png"));

    private  Bitmap maximizeIcon => AppData.Settings.DarkModeEnabled
        ? new Bitmap(Path.Combine(AppData.AssetPath, "DarkMode", "fullscreen-darkmode.png"))
        : new Bitmap(Path.Combine(AppData.AssetPath, "LightMode", "fullscreen-lightmode.png"));
    
        private  Bitmap minimizeIcon => AppData.Settings.DarkModeEnabled 
            ? new Bitmap(Path.Combine(AppData.AssetPath, "DarkMode", "minimize-darkmode.png")) 
            : new Bitmap(Path.Combine(AppData.AssetPath, "LightMode", "minimize-lightmode.png"));
        

    public TitleBarControl()
    {
        InitializeComponent();
        
        SetIcons();
        
        App.Current.ActualThemeVariantChanged += (s, e) =>
        {
            SetIcons();
        };
    }

    public void Initialize(Window window)
    {
        _window = window;
        DataContext = window;
    }

    private void TitleBarDrag(object? sender, PointerPressedEventArgs e)
    {
        _window?.BeginMoveDrag(e);
    }

    private void MinimizeClick(object? sender, RoutedEventArgs e)
    {
        if (_window != null)
            _window.WindowState = WindowState.Minimized;
    }

    private void MaximizeClick(object? sender, RoutedEventArgs e)
    {
        if (_window != null)
            _window.WindowState = _window.WindowState == WindowState.Maximized
                ? WindowState.Normal
                : WindowState.Maximized;
    }

    private void CloseClick(object? sender, RoutedEventArgs e)
    {
        _window?.Close();
    }

    private void SetIcons()
    {
        CloseIcon.Source = closeIcon;
        MaximizeIcon.Source = maximizeIcon;
        MinimizeIcon.Source = minimizeIcon;
    }
}