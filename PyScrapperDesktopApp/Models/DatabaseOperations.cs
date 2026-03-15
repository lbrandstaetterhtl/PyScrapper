using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;

namespace PyScrapperDesktopApp.Models;

public class DatabaseOperations
{
    private static string DatabaseFilePath = AppData.DataPath + @"\Data.sqlite";
    
    static SqliteConnection _connection = new($"Data Source={DatabaseFilePath}");
    
    public static async Task SaveDownloadedMedias(ObservableCollection<DownloadedMedia> downloadedMedias)
    {
        _connection.Open();
        
        var create = _connection.CreateCommand();
        
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
            
            var delete = _connection.CreateCommand();
            delete.CommandText = "DELETE FROM DownloadedMedias;";
            delete.ExecuteNonQuery();
            
            foreach (var media in downloadedMedias)
            {
                var insert = _connection.CreateCommand();
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
    }
    
    public static async Task<ObservableCollection<DownloadedMedia>> LoadDownloadedMedias()
    {
        var downloadedMedias = new ObservableCollection<DownloadedMedia>();
        
        _connection.Open();
        
        var create = _connection.CreateCommand();
        
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
        
        var select = _connection.CreateCommand();
        select.CommandText = "SELECT Id, Identifier, Url, MediaType, DownloadedAt, DownloadPath, IsPlayable FROM DownloadedMedias;";
        
        using (var reader = select.ExecuteReader())
        {
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
        }

        return downloadedMedias;
    }
}