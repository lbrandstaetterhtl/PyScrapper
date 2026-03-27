using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class CodecConverterWindow : Window
{
    public CodecConverterWindow(string inputPath, string outputPath, string message = "")
    {
        InitializeComponent();
        
        var vm = new CodecConverterWindowViewModel();
        DataContext = vm;
        
        vm.CloseRequested += () => Close();
        
        vm.InputFilePath = inputPath;
        vm.OutputFilePath = outputPath;
    }
    
    public async Task<bool> ShowDialogWithResult()
    {
        var tcs = new TaskCompletionSource<bool>();
        
        Closed += (s, e) =>
        {
            if (DataContext is CodecConverterWindowViewModel vm)
            {
                tcs.SetResult(!vm._cts.IsCancellationRequested);
            }
            else
            {
                tcs.SetResult(false);
            }
        };

        if (App.Current.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop) await ShowDialog(desktop.MainWindow);
        
        return await tcs.Task;
    }
}