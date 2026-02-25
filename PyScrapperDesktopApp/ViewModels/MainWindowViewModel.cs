using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    [RelayCommand]
    public async Task OpenSunoScrapWindow()
    {
        if (App.Current?.ApplicationLifetime is not IClassicDesktopStyleApplicationLifetime desktop)
            return;
        
        var SunoScrapWindow = new Views.SunoScrapWindow();
        await SunoScrapWindow.ShowDialog(desktop.MainWindow);
    }
}