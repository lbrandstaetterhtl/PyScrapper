using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using SQLitePCL;

namespace PyScrapperDesktopApp.Models;

public abstract class Database
{
    private static readonly AppLogger _logger = AppLogger.Instance;

    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMediasFromApi()
    {
        try
        {
            var downloadedMedias = new ObservableCollection<DownloadedMedia>();

            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);

            var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/getuser/downloadedmedias/{AppData.CurrentUser.Identifier}");
            var json = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                var medias = JsonSerializer.Deserialize<List<DownloadedMedia>>(json);

                if (medias != null)
                {
                    foreach (var media in medias)
                    {
                        downloadedMedias.Add(media);
                    }
                }
            }
            else
            {
                throw new Exception(response.ReasonPhrase);
            }

            return downloadedMedias;
        }
        catch (Exception e)
        {
            var log = new Message("Error while loading downloaded medias from API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return new ObservableCollection<DownloadedMedia>();
        }
    }

    public static async Task<ObservableCollection<Playlist>> LoadPlaylistsFromApi()
    {
        try
        {
            var playlists = new ObservableCollection<Playlist>();

            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);

            var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/getuser/playlists/{AppData.CurrentUser.Identifier}");

            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var apiPlaylists = JsonSerializer.Deserialize<List<GetPlaylistResponse>>(json);

                if (apiPlaylists != null)
                {
                    foreach (var playlist in apiPlaylists)
                    {
                        var newPlaylist = new Playlist(playlist.Name, playlist.Description, playlist.Identifier, playlist.UserIdentifier);
                        playlists.Add(newPlaylist);
                    }
                }
            }
            else
            {
                throw new Exception(response.ReasonPhrase);
            }

            return playlists;
        }
        catch (Exception e)
        {
            var log = new Message("Error while loading playlists from API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return new ObservableCollection<Playlist>();
        }
    }

    public static async Task<Settings> LoadSettingsFromApi()
    {
        try
        {
            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);

            var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/get/settings/{AppData.CurrentUser.Identifier}");

            var json = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                var settings = JsonSerializer.Deserialize<Settings>(json);

                if (settings != null)
                {
                    return settings;
                }
                else
                {
                    throw new Exception("Failed to deserialize settings from API response.");
                }
            }
            else
            {
                throw new Exception(response.ReasonPhrase);
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while loading settings from API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    public static async Task<List<PlaylistMedia>> LoadPlaylistMediaFromApi(string playlistIdentifier)
    {
        try
        {
            var playlistMediaList = new List<PlaylistMedia>();

            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);

            var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/get/playlistmedias/{playlistIdentifier}");

            if (response.IsSuccessStatusCode)
            {
                var json = await response.Content.ReadAsStringAsync();
                var apiPlaylistMedia = JsonSerializer.Deserialize<List<PlaylistMedia>>(json);

                if (apiPlaylistMedia != null)
                {
                    playlistMediaList.AddRange(apiPlaylistMedia);
                }
            }
            else
            {
                throw new Exception(response.ReasonPhrase);
            }

            return playlistMediaList;
        }
        catch (Exception e)
        {
            var log = new Message("Error while loading playlist media from API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    public static async Task<List<PlaylistMedia>> LoadAllPlaylistMedias(List<Playlist> playlists)
    {
        List<PlaylistMedia> allPlaylistMedias = new List<PlaylistMedia>();
        foreach (var playlist in playlists)
        {
            var media = await LoadPlaylistMediaFromApi(playlist.Identifier);
            allPlaylistMedias.AddRange(media);
        }

        return allPlaylistMedias;
    }

    public static async Task<DownloadedMedia> CreateDownloadedMedia(CreateDownloadedMediaRequest req)
    {
        try
        {
            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);   

            var jsonContent = JsonSerializer.Serialize(req);
            var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/create/downloadedmedia", content);  

            DownloadedMedia result;

            var json = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Downloaded media created successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                var deserialized = JsonSerializer.Deserialize<CreateResponse>(json);

                string identifier = deserialized?.Identifier ?? throw new Exception("Failed to deserialize identifier from API response.");

                DateTime downloadedAt = DateTime.Parse(req.DownloadedAt);

                result = new DownloadedMedia(AppData.CurrentUser.Identifier, req.Title, req.Url, req.MediaType, downloadedAt, req.DownloadPath, req.IsPlayable, identifier);

                return result;
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while creating downloaded media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }
    
    public static async Task<Playlist> CreatePlaylist(CreatePlaylistRequest req)
    {
        try
        {
            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey); 

            var jsonContent = JsonSerializer.Serialize(req);
            var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/create/playlist/", content);   

            Playlist result;

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Playlist created successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                var json = await response.Content.ReadAsStringAsync();
                var deserialized = JsonSerializer.Deserialize<CreateResponse>(json);

                string identifier = deserialized?.Identifier ?? throw new Exception("Failed to deserialize identifier from API response.");

                result = new Playlist(req.Name, req.Description, identifier, AppData.CurrentUser.Identifier);

                return result;
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while creating playlist via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    public static async Task<PlaylistMedia> CreatePlaylistMedia(CreatePlaylistMediaRequest req)
    {
        try
        {
            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);   

            var jsonContent = JsonSerializer.Serialize(req);
            var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/create/playlistmedia", content);   

            PlaylistMedia result;

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Playlist media created successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                var json = await response.Content.ReadAsStringAsync();
                var deserialized = JsonSerializer.Deserialize<CreatePlaylistMediaResponse>(json);

                int position = deserialized?.Position ?? throw new Exception("Failed to deserialize position from API response.");

                result = new PlaylistMedia(req.PlaylistIdentifier, req.MediaIdentifier, position);

                return result;
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while creating playlist media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }
    
    public static async Task DeleteDownloadedMedia(string identifier)
    {
        try
        {
            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);   

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/delete/downloadedmedia/?identifier={identifier}", null);   
            var json = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Downloaded media deleted successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while deleting downloaded media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }

    public static async Task DeletePlaylist(string identifier)
    {
        try
        {
            var content = new StringContent(JsonSerializer.Serialize(new { Identifier = identifier }), System.Text.Encoding.UTF8, "application/json");

            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);  

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/delete/playlist", content);   

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Playlist deleted successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while deleting playlist via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }

    public static async Task DeletePlaylistMedia(string playlistIdentifier, string mediaIdentifier)
    {
        try
        {
            var content = new StringContent(JsonSerializer.Serialize(new { PlaylistIdentifier = playlistIdentifier, MediaIdentifier = mediaIdentifier }), System.Text.Encoding.UTF8, "application/json");

            using var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);   

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/delete/playlistmedia", content);   

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Playlist media deleted successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }
        }
        catch (Exception e)
        {
            var log = new Message("Error while deleting playlist media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }

    public static async Task<Settings> CreateSettings(CreateSettingRequest req)
    {
        try
        {
            var content = new StringContent(JsonSerializer.Serialize(req), System.Text.Encoding.UTF8,
                "application/json");
            var client = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);   

            var response =
                await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/create/settings/", content);  
            var json = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Message("Default settings created successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);

                var deserialized = JsonSerializer.Deserialize<CreateResponse>(json);

                if (deserialized != null)
                {
                    var setting = new Settings(deserialized.Identifier)
                    {
                        DownloadPath = req.DefaultDownloadPath,
                        DarkModeEnabled = req.DarkModeEnabled,
                        ScanFolderOnStartup = req.ScanFolderOnStartup
                    };

                    return setting;
                }
                else
                {
                    throw new Exception("Failed to deserialize settings from API response.");
                }
            }
        }
        catch (Exception ex)
        {
            var log = new Message("Error while creating settings via API: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    public static async Task<User> GetUser(string identifier)
    {
        var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);
        var response = await client.GetAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/get/user/{identifier}");

        if (!response.IsSuccessStatusCode)
        {
            throw new Exception(response.ReasonPhrase);
        }
        else
        {
            var log = new Message("User retrieved successfully via API.", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);

            var json = await response.Content.ReadAsStringAsync();
            var user = JsonSerializer.Deserialize<User>(json);

            if (user != null)
            {
                return user;
            }
            else
            {
                throw new Exception("Failed to deserialize user from API response.");
            }
        }
    }

    public static async Task<bool> SaveUserData(SaveDataRequest req)
    {
            using var client  = new HttpClient();
            client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);

            var content = new StringContent(JsonSerializer.Serialize(req), System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/save", content);

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }

            var log = new Message("User data saved successfully via API.", DateTime.Now, "INFO");
            _logger.LogNewMassage(log);
            return true;
    }

    public static async Task<bool> SetUserLoggedIn()
    {
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-Admin-Key", AppData.Config.ApiKey);   

        var content = new StringContent("{}", System.Text.Encoding.UTF8, "application/json");
        var response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/set/user/loggedIn?identifier={AppData.CurrentUser.Identifier}",  content);  

        if (!response.IsSuccessStatusCode)
        {
            throw new Exception(response.ReasonPhrase);
        }

        response = await client.PostAsync($"{AppData.Config.ServerUrl}:{AppData.Config.ServerPort}/set/user/lastLoggedIn?identifier={AppData.CurrentUser.Identifier}",  content); 

        if (!response.IsSuccessStatusCode)
        {
            throw new Exception(response.ReasonPhrase);
        }
        
        return true;
    }
}