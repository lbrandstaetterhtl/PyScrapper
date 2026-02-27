using System;
using System.ComponentModel;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

public partial class InputWindowViewModel : ObservableObject
{
    private readonly Window _Window;

    [ObservableProperty] 
    private string _massage;
    
    [ObservableProperty]
    private string _inputText;

    public InputWindowViewModel(Window Window, string massage)
    {
        _Window = Window;
        Massage = massage;
    }
    
    [RelayCommand]
    private void Ok()
    {
        _Window.Close(InputText);
    }
    
    [RelayCommand]
    private void Cancel()
    {
        _Window.Close(null);
    }
}