using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class EditConfigWindow : Window
{
    public EditConfigWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new EditConfigWindowViewModel(AppData.Config, new DialogService(this));
        vm.CloseRequested += Close;
        DataContext = vm;
    }
}