using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

public partial class ConfirmationWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _message;

    private readonly Window _window;
    
    [RelayCommand]
    private void Confirm()
    {
        _window.Close(true);
    }

    [RelayCommand]
    private void Cancel()
    {
        _window.Close(false);
    }
    
    public ConfirmationWindowViewModel(Window window)
    {
        _window = window;
    }
}