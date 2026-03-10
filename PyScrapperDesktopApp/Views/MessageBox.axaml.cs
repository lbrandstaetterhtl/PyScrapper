using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class MessageBox : Window
{
    
    public MessageBox(string message)
    {
        InitializeComponent();
        Massage.Text = message;
        
        OkButton.Click += (_, _) => Close();
    }
}