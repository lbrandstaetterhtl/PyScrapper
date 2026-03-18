using System;
using System.Collections.ObjectModel;
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
            Connection.Open();
        
            var create = Connection.CreateCommand();
        
            create.CommandText =
                """
                CREATE TABLE IF NOT EXISTS DownloadedMedias (
                    Id INTEGER PRIMARY KEY,
                    Identifier TEXT,
                    Url TEXT,
                    MediaType TEXT,
                    DownloadedAt TEXT,
                    DownloadPath TEXT,
                    IsPlayable INTEGER
                )STRICT;
                """;

            create.ExecuteNonQuery();
            
            var delete = Connection.CreateCommand();
            delete.CommandText = "DELETE FROM DownloadedMedias;";
            delete.ExecuteNonQuery();
            
            foreach (var media in downloadedMedias)
            {
                var insert = Connection.CreateCommand();
                insert.CommandText =
                    """
                    INSERT INTO DownloadedMedias (Id, Identifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable)
                    VALUES ($id, $identifier, $url, $mediaType, $downloadedAt, $downloadPath, $isPlayable);
                    """;
                insert.Parameters.AddWithValue("$id", media.Id);
                insert.Parameters.AddWithValue("$identifier", media.Identifier);
                insert.Parameters.AddWithValue("$url", media.Url);
                insert.Parameters.AddWithValue("$mediaType", media.MediaType);
                insert.Parameters.AddWithValue("$downloadedAt", media.DownloadedAt.ToString("o"));
                insert.Parameters.AddWithValue("$downloadPath", media.DownloadPath);
                insert.Parameters.AddWithValue("$isPlayable", media.IsPlayable);
                
                insert.ExecuteNonQuery();
            }
            
            Connection.Close();
        }
        catch (Exception exception)
        {
            var logger = new AppLogger();
            var log = new Massage("Error while saving downloaded medias to database: " + exception.Message, DateTime.Now, "ERROR");
            logger.LogNewMassage(log);
        }
    }
    
    /// <summary>
    /// Loads the collection of downloaded media from the SQLite database, creating the necessary table if it doesn't exist and retrieving all records to populate an ObservableCollection of DownloadedMedia objects.
    /// </summary>
    /// <returns name="downloadedMedias"></returns>
    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMedias()
    {
        var downloadedMedias = new ObservableCollection<DownloadedMedia>();
        
        Connection.Open();
        
        var create = Connection.CreateCommand();
        
        create.CommandText =
            """
            CREATE TABLE IF NOT EXISTS DownloadedMedias (
                Id INTEGER PRIMARY KEY,
                Identifier TEXT,
                Url TEXT,
                MediaType TEXT,
                DownloadedAt TEXT,
                DownloadPath TEXT,
                IsPlayable INTEGER
            )STRICT;
            """;

        create.ExecuteNonQuery();
        
        var select = Connection.CreateCommand();
        select.CommandText = "SELECT Id, Identifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable FROM DownloadedMedias;";

        await using var reader = await select.ExecuteReaderAsync();
        while (reader.Read())
        {
            var media = new DownloadedMedia(
                reader.GetString(2), // Url
                reader.GetString(3), // MediaType
                DateTime.Parse(reader.GetString(4)), // DownloadedAt
                reader.GetString(5), // DownloadPath
                reader.GetBoolean(6), // IsPlayable
                reader.GetString(1) // Identifier
            )
            {
                Id = reader.GetInt32(0) // Id
            };
                
            downloadedMedias.Add(media);
        }
        
        Connection.Close();
        return downloadedMedias;
    }

    /// <summary>
    /// Loads the collection of downloaded media from the SQLite database, creating the necessary table if it doesn't exist and retrieving distinct records based on the Identifier to populate an ObservableCollection of DownloadedMedia objects without duplicates.
    /// </summary>
    /// <returns name="downloadedMedias"></returns>
    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMediasNoDuplicates()
    {
        var downloadedMedias = new ObservableCollection<DownloadedMedia>();
        
        Connection.Open();
        
        var create = Connection.CreateCommand();
        
        create.CommandText =
            """
            CREATE TABLE IF NOT EXISTS DownloadedMedias (
                Id INTEGER PRIMARY KEY,
                Identifier TEXT,
                Url TEXT,
                MediaType TEXT,
                DownloadedAt TEXT,
                DownloadPath TEXT,
                IsPlayable INTEGER
            )STRICT;
            """;
        
        create.ExecuteNonQuery();
        
        var select = Connection.CreateCommand();
        select.CommandText = "SELECT DISTINCT Id, Identifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable FROM DownloadedMedias GROUP BY Identifier;";
        
        await using var reader = await select.ExecuteReaderAsync();
        while (reader.Read())
        {
            var media = new DownloadedMedia(
                reader.GetString(2), // Url
                reader.GetString(3), // MediaType
                DateTime.Parse(reader.GetString(4)), // DownloadedAt
                reader.GetString(5), // DownloadPath
                reader.GetBoolean(6), // IsPlayable
                reader.GetString(1) // Identifier
            )
            {
                Id = reader.GetInt32(0) // Id
            };
            
            downloadedMedias.Add(media);
        }

        Connection.Close();
        
        return downloadedMedias;
    }
    
    
}