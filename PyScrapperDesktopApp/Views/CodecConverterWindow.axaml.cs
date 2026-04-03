using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class CodecConverterWindow : Window
{
    public CodecConverterWindow(string inputPath, string outputPath)
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        var vm = new CodecConverterWindowViewModel(this);
        DataContext = vm;
        
        vm.InputFilePath = inputPath;
        vm.OutputFilePath = outputPath;
    }
}