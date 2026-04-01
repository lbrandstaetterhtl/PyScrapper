using Avalonia.Controls;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

public partial class ConfirmationWindowViewModel : ObservableObject
{
    [ObservableProperty]
    private string _message;

    private readonly Window _window;
    
    /// <summary>
    /// Closes the confirmation window and returns true to indicate that the user confirmed the action.
    /// This method is called when the user clicks the "Confirm" button in the UI, signaling that they agree to proceed with the action being confirmed.
    /// </summary>
    [RelayCommand]
    private void Confirm()
    {
        _window.Close(true);
    }

    /// <summary>
    /// Closes the confirmation window and returns false to indicate that the user canceled the action.
    /// This method is called when the user clicks the "Cancel" button in the UI, signaling that they do not agree to proceed with the action being confirmed.
    /// </summary>
    [RelayCommand]
    private void Cancel()
    {
        _window.Close(false);
    }
    
    /// <summary>
    /// Constructor for the ConfirmationWindowViewModel class, which initializes the view model with a reference to the window and a message to display as the confirmation prompt for the user.
    /// The message is used to inform the user about the action they are being asked to confirm (e.g., "Are you sure you want to delete this file?").
    /// </summary>
    /// <param name="window"></param>
    public ConfirmationWindowViewModel(Window window, string message)
    {
        _window = window;
        _message = message;
    }
}