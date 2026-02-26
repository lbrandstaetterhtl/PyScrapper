using Avalonia.Controls;

namespace PyScrapperDesktopApp.Views;

public partial class MassageBox : Window
{
    private string _message;
    
    public MassageBox(string message)
    {
        InitializeComponent();
        _message = message;
        Massage.Text = _message;
        
        OkButton.Click += (sender, args) => Close();
    }
}