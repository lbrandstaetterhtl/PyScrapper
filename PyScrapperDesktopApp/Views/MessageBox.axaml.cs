using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class MessageBox : Window
{
    
    public MessageBox(string message)
    {
        if (Design.IsDesignMode) return;
        
        InitializeComponent();
        TitleBar.Initialize(this);
        Massage.Text = message;
        
        OkButton.Click += (_, _) => Close();
    }
}