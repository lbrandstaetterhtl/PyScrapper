using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

/// <summary>
/// Class responsible for managing the state and logic of the InputWindow, which prompts the user to enter a string input (e.g., a file path) and returns that input when the user clicks "OK". It also handles the cancellation of the input when the user clicks "Cancel", returning null in that case.
/// The class uses data binding to update the UI with the prompt message and the user's input in real-time.
/// </summary>
public partial class InputWindowViewModel : ObservableObject
{
    private readonly Window _Window;

    [ObservableProperty] 
    private string _massage;
    
    [ObservableProperty]
    private string _inputText;

    /// <summary>
    /// Constructor for the InputWindowViewModel, which initializes the view model with a reference to the window and a message to display as a prompt for the user. The message is used to inform the user what kind of input is expected (e.g., "Enter a valid file path (.mp3)").
    /// The constructor also checks if the application is in design mode to avoid executing code that should only run at runtime.
    /// </summary>
    /// <param name="Window"></param>
    /// <param name="massage"></param>
    public InputWindowViewModel(Window Window, string massage)
    {
        if (Design.IsDesignMode) return;
        
        _Window = Window;
        Massage = massage;
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the "OK" button. It closes the window and returns the user's input text as the result of the dialog.
    /// This allows the calling code to receive the input provided by the user and use it for further processing (e.g., opening a media file in the media player).
    /// </summary>
    [RelayCommand]
    private void Ok()
    {
        _Window.Close(InputText);
    }
    
    /// <summary>
    /// Command method that is executed when the user clicks the "Cancel" button.
    /// It closes the window and returns null as the result of the dialog, indicating that the user has canceled the input operation.
    /// </summary>
    [RelayCommand]
    private void Cancel()
    {
        _Window.Close(null);
    }
}