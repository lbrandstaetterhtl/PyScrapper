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

public class Database
{
    private static readonly AppLogger _logger = new();
    
    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMediasFromApi()
    {
        try
        {
            var downloadedMedias = new ObservableCollection<DownloadedMedia>();

            using var client = new HttpClient();

            var response = await client.GetAsync($"{AppData.Settings.ServerUrl}/getuser/downloadedmedias/{AppData.AdminKey}?user_identifier={AppData.CurrentUser.Identifier}");
            var json = await response.Content.ReadAsStringAsync();
            
            _logger.LogDebugMessage(new Massage($"Response from API: {json}", DateTime.Now, "INFO"));

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
            var log = new Massage("Error while loading downloaded medias from API: " + e.Message, DateTime.Now, "ERROR");
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

            var response = await client.GetAsync($"{AppData.Settings.ServerUrl}/getuser/playlists/{AppData.AdminKey}?user_identifier={AppData.CurrentUser.Identifier}");

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
            var log = new Massage("Error while loading playlists from API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return new ObservableCollection<Playlist>();
        }
    }
    
    public static async Task<Settings> LoadSettingsFromApi()
    {
        try
        {
            using var client = new HttpClient();

            var response = await client.GetAsync($"http://127.0.0.1:8765/get/settings/{AppData.CurrentUser.Identifier}");

            var json = await response.Content.ReadAsStringAsync();
            
            _logger.LogDebugMessage(new Massage($"Response from API: {json}", DateTime.Now, "INFO"));
            
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
            var log = new Massage("Error while loading settings from API: " + e.Message, DateTime.Now, "ERROR");
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

            var response = await client.GetAsync($"{AppData.Settings.ServerUrl}/get/playlistmedias/{playlistIdentifier}");

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
            var log = new Massage("Error while loading playlist media from API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    public async Task<List<PlaylistMedia>> LoadAllPlaylistMedias(string playlistIdentifier, List<Playlist> playlists)
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

            var jsonContent = JsonSerializer.Serialize(req);
            var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/create/downloadedmedia/{AppData.AdminKey}", content);

            DownloadedMedia result;
            
            var json = await response.Content.ReadAsStringAsync();
            
            _logger.LogDebugMessage(new Massage($"Response from API CreateDownloadedMedia: {json}, request: {content}", DateTime.Now, "INFO"));

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Downloaded media created successfully via API.", DateTime.Now, "INFO");
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
            var log = new Massage("Error while creating downloaded media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }
    
    public static async Task<Playlist> CreatePlaylist(CreatePlaylistRequest req)
    {
        try
        {
            using var client = new HttpClient();

            var jsonContent = JsonSerializer.Serialize(req);
            var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/create/playlist/{AppData.AdminKey}", content);

            Playlist result;

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Playlist created successfully via API.", DateTime.Now, "INFO");
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
            var log = new Massage("Error while creating playlist via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }
    
    public static async Task<PlaylistMedia> CreatePlaylistMedia(CreatePlaylistMediaRequest req)
    {
        try
        {
            using var client = new HttpClient();

            var jsonContent = JsonSerializer.Serialize(req);
            var content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json");

            var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/create/playlistmedia/{AppData.AdminKey}", content);

            PlaylistMedia result;

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Playlist media created successfully via API.", DateTime.Now, "INFO");
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
            var log = new Massage("Error while creating playlist media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }
    
    public static async Task DeleteDownloadedMedia(string identifier)
    {
        try
        {
            using var client = new HttpClient();

            var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/delete/downloadedmedia/{AppData.AdminKey}?identifier={identifier}", null);
            var json = await response.Content.ReadAsStringAsync();
            _logger.LogDebugMessage(new Massage($"Response from API DeleteDownloadedMedia: {json}", DateTime.Now, "INFO"));

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Downloaded media deleted successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }
        }
        catch (Exception e)
        {
            var log = new Massage("Error while deleting downloaded media via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }
    
    public static async Task DeletePlaylist(string identifier)
    {
        try
        {
            var content = new StringContent(JsonSerializer.Serialize(new { Identifier = identifier }), System.Text.Encoding.UTF8, "application/json");
            
            using var client = new HttpClient();

            var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/delete/playlist/{AppData.AdminKey}", content);

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Playlist deleted successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }
        }
        catch (Exception e)
        {
            var log = new Massage("Error while deleting playlist via API: " + e.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
        }
    }
    
    public static async Task DeletePlaylistMedia(string playlistIdentifier, string mediaIdentifier)
    {
        try
        {
            var content = new StringContent(JsonSerializer.Serialize(new { PlaylistIdentifier = playlistIdentifier, MediaIdentifier = mediaIdentifier }), System.Text.Encoding.UTF8, "application/json");
            
            using var client = new HttpClient();

            var response = await client.PostAsync($"{AppData.Settings.ServerUrl}/delete/playlistmedia/{AppData.AdminKey}", content);

            if (!response.IsSuccessStatusCode)
            {
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Playlist media deleted successfully via API.", DateTime.Now, "INFO");
                _logger.LogNewMassage(log);
            }
        }
        catch (Exception e)
        {
            var log = new Massage("Error while deleting playlist media via API: " + e.Message, DateTime.Now, "ERROR");
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
            //TODO: not hardcoded url
            var response =
                await client.PostAsync($"http://127.0.0.1:8765/create/settings/{AppData.AdminKey}", content);
            var json = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogDebugMessage(new Massage(json, DateTime.Now, "ERROR"));
                throw new Exception(response.ReasonPhrase);
            }
            else
            {
                var log = new Massage("Default settings created successfully via API.", DateTime.Now, "INFO");
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
            var log = new Massage("Error while creating settings via API: " + ex.Message, DateTime.Now, "ERROR");
            _logger.LogNewMassage(log);
            return null;
        }
    }

    
    public static async Task<User> GetUser(string identifier)
    {
        var client = new HttpClient();
        var response = await client.GetAsync($"{AppData.Settings.ServerUrl}/get/user/{identifier}");
        
        _logger.LogDebugMessage(new Massage(response.ReasonPhrase, DateTime.Now, "INFO"));
        
        if (!response.IsSuccessStatusCode)
        {
            throw new Exception(response.ReasonPhrase);
        }
        else
        {
            var log = new Massage("User retrieved successfully via API.", DateTime.Now, "INFO");
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
}

/*
/// <summary>
/// Class responsible for handling database operations related to downloaded media, including saving and loading media information to and from a SQLite database.
/// </summary>
public abstract class DatabaseOperations
{
    private static readonly string DatabaseFilePath = AppData.DataPath + @"\Data.sqlite";
    
    static readonly SqliteConnection Connection = new($"Data Source={DatabaseFilePath}");
    
    private static readonly AppLogger Logger = new();
    
    /// <summary>
    /// Saves the provided collection of downloaded media to the SQLite database.
    /// It creates the necessary table if it doesn't exist, clears existing records, and inserts the new media data.
    /// If any errors occur during this process, they are logged using the AppLogger class.
    /// </summary>
    /// <param name="downloadedMedias"></param>
    public static void SaveDownloadedMedias(ObservableCollection<DownloadedMedia> downloadedMedias)
    {
        try
        {
            foreach (var media in downloadedMedias)
            {
                
            }
        }
        catch (Exception exception)
        {
            var log = new Massage("Error while saving downloaded medias to database: " + exception.Message, DateTime.Now, "ERROR");
            Logger.LogNewMassage(log);
        }
    }
    
    /// <summary>
    /// Loads the collection of downloaded media from the SQLite database, creating the necessary table if it doesn't exist and retrieving all records to populate an ObservableCollection of DownloadedMedia objects.
    /// </summary>
    /// <returns name="downloadedMedias"></returns>
    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMedias()
    {
        var downloadedMedias = new ObservableCollection<DownloadedMedia>();

        using var client = new HttpClient();
        
        var response = await client.GetAsync("http://127.0.0.0:8765/getall/downloadedmedias/pyscrapper_K4i1MwQkWUVibOArEC6WtbRibTPlCBYR");
        
        if (response.IsSuccessStatusCode)
        {
            var json = await response.Content.ReadAsStringAsync();
            var medias = JsonSerializer.Deserialize<List<DownloadedMedia>>(json);

            if (medias != null)
            {
                foreach (var media in medias)
                {
                    if (media.UserIdentifier == AppData.CurrentUser.Identifier)
                    {
                        downloadedMedias.Add(media);
                    }
                }
            }
        }
        else
        {
            var log = new Massage("Error while loading downloaded medias from API: " + response.ReasonPhrase, DateTime.Now, "ERROR");
            Logger.LogNewMassage(log);
        }
        
        return downloadedMedias;
    }
    
    /// <summary>
    /// Loads the collection of playlists from the SQLite database, creating the necessary table if it doesn't exist and retrieving distinct records based on the Name to populate an ObservableCollection of Playlist objects without duplicates.
    /// </summary>
    /// <returns name="playlists"></returns>
    public static async Task<ObservableCollection<Playlist>> LoadPlaylistsNoDuplicates()
    {
        try
        {
            if (!File.Exists(DatabaseFilePath))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(DatabaseFilePath));
                File.Create(DatabaseFilePath).Close();
            }
            
            var playlists = new ObservableCollection<Playlist>();

            Connection.Open();

            var createCommand = Connection.CreateCommand();

            createCommand.CommandText =
                """
                    CREATE TABLE IF NOT EXISTS Playlists (
                        Id INTEGER PRIMARY KEY,
                        Name TEXT,
                        Description TEXT,
                        MediaIds TEXT,
                        PlayableMediaIds TEXT
                    )STRICT;
                """;

            createCommand.ExecuteNonQuery();

            var selectCommand = Connection.CreateCommand();

            selectCommand.CommandText =
                "SELECT DISTINCT Id, Name, Description, MediaIds, PlayableMediaIds FROM Playlists GROUP BY Name;";

            await using var reader = await selectCommand.ExecuteReaderAsync();

            while (reader.Read())
            {
                var playlist = new Playlist(
                    JsonSerializer.Deserialize<List<int>>(reader.GetString(3)),
                    reader.GetString(1), // Name
                    reader.IsDBNull(2) ? null : reader.GetString(2)
                )
                {
                    Id = reader.GetInt32(0),
                    PlayableMediaIds = JsonSerializer.Deserialize<List<int>>(reader.GetString(4))
                };

                playlists.Add(playlist);
            }

            Connection.Close();

            return playlists;
        }
        catch (Exception exception)
        {
            var errorLog = new Massage("Error while loading Playlists" + exception.Message, DateTime.Now, "ERROR");
            Logger.LogNewMassage(errorLog);
            return null;
        }
    }
    
    /// <summary>
    /// Saves the provided collection of playlists to the SQLite database. It creates the necessary table if it doesn't exist, clears existing records, and inserts the new playlist data. If any errors occur during this process, they are logged using the AppLogger class.
    /// </summary>
    /// <param name="playlists"></param>
    public static void SavePlaylists(ObservableCollection<Playlist> playlists)
    {
        try
        {
            if (!File.Exists(DatabaseFilePath))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(DatabaseFilePath));
                File.Create(DatabaseFilePath).Close();
            }
            
            Connection.Open();
            
            var createCommand = Connection.CreateCommand();

            createCommand.CommandText =
                """
                    CREATE TABLE IF NOT EXISTS Playlists (
                        Id INTEGER PRIMARY KEY,
                        Name TEXT,
                        Description TEXT,
                        MediaIds TEXT,
                        PlayableMediaIds TEXT
                    )STRICT;
                """;
        
            createCommand.ExecuteNonQuery();
            
            var deleteCommand = Connection.CreateCommand();
            deleteCommand.CommandText = "DELETE FROM Playlists;";
            deleteCommand.ExecuteNonQuery();
            
            foreach (var playlist in playlists)
            {
                var insertCommand = Connection.CreateCommand();
                insertCommand.CommandText =
                    """
                    INSERT INTO Playlists (Id, Name, Description, MediaIds, PlayableMediaIds)
                    VALUES ($id, $name, $description, $mediaIds, $playableMediaIds);
                    """;
                insertCommand.Parameters.AddWithValue("$id", playlist.Id);
                insertCommand.Parameters.AddWithValue("$name", playlist.Name);
                insertCommand.Parameters.AddWithValue("$description", playlist.Description);
                insertCommand.Parameters.AddWithValue("$mediaIds", JsonSerializer.Serialize(playlist.MediaIds));
                insertCommand.Parameters.AddWithValue("$playableMediaIds", JsonSerializer.Serialize(playlist.PlayableMediaIds));
                
                insertCommand.ExecuteNonQuery();
            }
            
            Connection.Close();
        }
        catch (Exception e)
        {
            var log = new Massage("Error while saving playlists: " + e.Message, DateTime.Now, "ERROR");
            Logger.LogNewMassage(log);
        }
    }

    /// <summary>
    /// Loads the application settings from the SQLite database, creating the necessary table if it doesn't exist and retrieving the distinct record to populate a Settings object.
    /// If any errors occur during this process, they are logged using the AppLogger class, and a default Settings object is returned.
    /// </summary>
    /// <returns></returns>
    public static async Task<Settings> LoadSettings()
    {
        try
        {
            if (!File.Exists(DatabaseFilePath))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(DatabaseFilePath));
                File.Create(DatabaseFilePath).Close();
            }
            
            var settings = new Settings();
            settings.SetDefaultSettings();
            
            Connection.Open();
            
            var createCommand = Connection.CreateCommand();
            
            createCommand.CommandText = 
                """
                    CREATE TABLE IF NOT EXISTS Settings (
                        Id INTEGER PRIMARY KEY,
                        DownloadPath TEXT,
                        DarkModeEnabled INTEGER,
                        ScanFolderOnStartup INTEGER
                    )STRICT;
                """;
            
            createCommand.ExecuteNonQuery();
            
            var selectCommand = Connection.CreateCommand();
            
            selectCommand.CommandText = "SELECT DISTINCT Id, DownloadPath, DarkModeEnabled, ScanFolderOnStartup FROM Settings LIMIT 1;";
            
            await using var reader = await selectCommand.ExecuteReaderAsync();

            while (await reader.ReadAsync())
            {
                var id = reader.GetInt32(0);
                var downloadPath = reader.GetString(1);
                var darkModeEnabled = reader.GetBoolean(2);
                var scanFolderOnStartup = reader.GetBoolean(3);
                settings = new Settings()
                {
                    Id = id,
                    DownloadPath = downloadPath,
                    DarkModeEnabled = darkModeEnabled,
                    ScanFolderOnStartup = scanFolderOnStartup
                };
            }
            
            Connection.Close();
            
            return settings;
        }
        catch (Exception e)
        {
            var log = new Massage("Error while loading settings: " + e.Message, DateTime.Now, "ERROR");
            Logger.LogNewMassage(log);
            Settings settings = new();
            settings.SetDefaultSettings();
            return settings;
        }
    }

    /// <summary>
    /// Saves the provided settings to the SQLite database.
    /// It creates the necessary table if it doesn't exist, clears existing records, and inserts the new settings data.
    /// If any errors occur during this process, they are logged using the AppLogger class.
    /// </summary>
    /// <param name="settings"></param>
    public static void SaveSettings(Settings settings)
    {
        try
        {
            if (!File.Exists(DatabaseFilePath))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(DatabaseFilePath));
                File.Create(DatabaseFilePath).Close();
            }
            
            Connection.Open();
            
            var createCommand = Connection.CreateCommand();
            
            createCommand.CommandText =
                """
                    CREATE TABLE IF NOT EXISTS Settings (
                        Id INTEGER PRIMARY KEY,
                        DownloadPath TEXT,
                        DarkModeEnabled INTEGER,
                        ScanFolderOnStartup INTEGER
                    )STRICT;
                """;
                
            
            var deleteCommand  = Connection.CreateCommand();
            deleteCommand.CommandText =  "DELETE FROM Settings;";
            deleteCommand.ExecuteNonQuery();
            
            var insertCommand = Connection.CreateCommand();
            insertCommand.CommandText =
                "INSERT INTO Settings (Id, DownloadPath, DarkModeEnabled,  ScanFolderOnStartup)" +
                "VALUES ($id, $downloadPath,  $darkModeEnabled, $scanFolderOnStartup);";
            insertCommand.Parameters.AddWithValue("$id", settings.Id);
            insertCommand.Parameters.AddWithValue("$downloadPath", settings.DownloadPath);
            insertCommand.Parameters.AddWithValue("$darkModeEnabled", settings.DarkModeEnabled);
            insertCommand.Parameters.AddWithValue("$scanFolderOnStartup", settings.ScanFolderOnStartup);
            
            insertCommand.ExecuteNonQuery();
            
            Connection.Close();
        }
        catch (Exception e)
        {
            var log = new Massage("Error while saving settings: " + e.Message, DateTime.Now, "ERROR");
            Logger.LogNewMassage(log);
        }
    }
}
*/