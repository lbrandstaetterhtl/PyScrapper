using System;
using System.Threading;
using Avalonia.Controls;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class ProgressBarWindow : Window
{
    public ProgressBarWindow()
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this, onClose: () => OnCancel.Invoke());
        
        var vm = new ViewModels.ProgressBarWindowViewModel(this);
        vm.CloseRequested += Close;
        DataContext = vm;
    }

    public Action OnCancel { get; set; }
}
