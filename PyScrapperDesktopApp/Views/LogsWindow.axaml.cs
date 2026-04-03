using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class LogsWindow : Window
{
    public LogsWindow(string logs, string label)
    {
        InitializeComponent();
        TitleBar.Initialize(this);
        
        if (Design.IsDesignMode) return;
        
        Logs.Text = logs;
        
        Label.Text = label;
    }
}