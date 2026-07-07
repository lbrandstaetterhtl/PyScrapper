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

namespace PyScrapperDesktopApp.Models;

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