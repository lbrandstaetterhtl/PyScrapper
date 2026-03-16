using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace PyScrapperDesktopApp.Models;

public class DatabaseOperations
{
    private static string DatabaseFilePath = AppData.DataPath + @"\Data.sqlite";
    
    static readonly SqliteConnection Connection = new($"Data Source={DatabaseFilePath}");
    
    public static Task SaveDownloadedMedias(ObservableCollection<DownloadedMedia> downloadedMedias)
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
                    IsPlayable BOOLEAN
                );
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

            return Task.CompletedTask;
        }
        catch (Exception exception)
        {
            return Task.FromException(exception);
        }
    }
    
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
                IsPlayable BOOLEAN
            );
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

    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMediasNoDuplicates()
    {
        var medias = new ObservableCollection<DownloadedMedia>();
        
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
                IsPlayable BOOLEAN
            );
            """;
        
        create.ExecuteNonQuery();
        
        var select = Connection.CreateCommand();
        select.CommandText = "SELECT DISTINCT Id, Identifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable FROM DownloadedMedias GROUP BY Identifier;";
        
        using var reader = select.ExecuteReader();
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
            
            medias.Add(media);
        }

        Connection.Close();
        
        return medias;
    }
    
    
}