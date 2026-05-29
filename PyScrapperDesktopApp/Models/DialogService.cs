using System.Threading.Tasks;
using Avalonia.Controls;
using PyScrapperDesktopApp.Views;

namespace PyScrapperDesktopApp.Models;

public class DialogService(Window owner) : Interfaces.IDialogService
{
    public async Task ShowAlertAsync(string message)
        => await new MessageBox(message).ShowDialog(owner);

    public async Task<bool> ConfirmAsync(string message) =>
        await new ConfirmationWindow(message).ShowDialog<bool>(owner);
    
    public async Task <string?> AskInputAsync(string message) =>
        await new InputWindow(message).ShowDialog<string?>(owner);
}
