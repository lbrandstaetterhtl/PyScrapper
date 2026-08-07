using System.Threading.Tasks;
using Avalonia.Controls;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

public class DialogService(Window owner) : Interfaces.IDialogService
{
    /// <summary>
    /// Shows an alert dialog with the specified message. The dialog is displayed as a modal window, and the method awaits the user's response before returning.
    /// </summary>
    /// <param name="message"></param>
    public async Task ShowAlertAsync(string message)
        => await new MessageBox(message).ShowDialog(owner);

    /// <summary>
    /// Shows a confirmation dialog with the specified message. The dialog is displayed as a modal window,
    /// and the method awaits the user's response before returning a boolean value indicating whether the user confirmed (true) or canceled (false).
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public async Task<bool> ConfirmAsync(string message) =>
        await new ConfirmationWindow(message).ShowDialog<bool>(owner);
    
    /// <summary>
    /// Shows an input dialog with the specified message. The dialog is displayed as a modal window,
    /// and the method awaits the user's input before returning the entered string value.
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public async Task <string?> AskInputAsync(string message) =>
        await new InputWindow(message).ShowDialog<string?>(owner);
}
