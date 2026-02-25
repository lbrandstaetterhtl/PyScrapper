using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.Input;

namespace PyScrapperDesktopApp.ViewModels;

public partial class MainWindowViewModel : ViewModelBase
{
    private static readonly HttpClient client = new();
    private const string serverUrl = "127.0.0.1:8765";
    
    public async void ScrapSuno(string url, string mediaType)
    {
        if (string.IsNullOrWhiteSpace(url)) return;
        if (mediaType != ".mp3" && mediaType != ".mp4") return;

        try
        {
            var requestData = new
            {
                provider = "suno",
                url = url,
                mediaType = mediaType
            };
            
            await client.PostAsJsonAsync($"http://{serverUrl}/download", requestData);
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
    }
}