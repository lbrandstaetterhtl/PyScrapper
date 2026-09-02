using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Security.Cryptography;
using System.Text;
using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// Encrypts/decrypts strings using Windows DPAPI. The key is derived from the
/// current Windows user — nothing needs to be stored or managed by us.
/// Only the same Windows user on the same machine can decrypt.
/// </summary>
public static class SecretProtector
{
    private static readonly byte[] Entropy = "PyScrapper.v1"u8.ToArray();

    /// <summary>
    /// Encrypts a plain text string using Windows DPAPI and returns the encrypted string in Base64 format.
    /// </summary>
    /// <param name="plainText"></param>
    /// <returns></returns>
    public static string Encrypt(string plainText)
    {
        if (string.IsNullOrEmpty(plainText))
            return "";

        try
        {
            byte[] plainBytes = Encoding.UTF8.GetBytes(plainText);
            byte[] encrypted = ProtectedData.Protect(plainBytes, Entropy, DataProtectionScope.CurrentUser);
            return Convert.ToBase64String(encrypted);
        }
        catch (Exception ex)
        {
            var log = new Message("Failed to encrypt base64 string", DateTime.Now, "ERROR");
            AppLogger.Instance.LogNewMassage(log);
            return "";
        }
    }

    /// <summary>
    /// Decrypts a Base64-encoded encrypted string using Windows DPAPI and returns the original plain text string.
    /// </summary>
    /// <param name="encryptedBase64"></param>
    /// <returns></returns>
    public static string Decrypt(string encryptedBase64)
    {
        if (string.IsNullOrEmpty(encryptedBase64))
            return "";

        try
        {
            byte[] encrypted = Convert.FromBase64String(encryptedBase64);
            byte[] plainBytes = ProtectedData.Unprotect(encrypted, Entropy, DataProtectionScope.CurrentUser);
            return Encoding.UTF8.GetString(plainBytes);
        }
        catch (Exception ex)
        {
            var log = new Message("Failed to decrypt base64 string", DateTime.Now, "ERROR");
            AppLogger.Instance.LogNewMassage(log);
            return "";
        }
    }
    
    public static string GenerateApiKey()
    {
        // Generate a new API key with a prefix and a random GUID (comment if in production)
        /*var apikey = "pyscrapper_" + Guid.NewGuid().ToString().Substring(0, 8);
        var encryptedKey = Encrypt(apikey);
        return encryptedKey;*/

        return "pyscrapper_789fhn897hnz6f709n87nuf"; // Return a fixed API key for production
    }
}

/// <summary>
/// Represents the application configuration, including server settings, API key, and last logged-in user.
/// </summary>
public class AppConfig
{
    [JsonPropertyName("ServerUrl")]
    public string? ServerUrl { get; set; }
    
    [JsonPropertyName("ServerPort")]
    public string? ServerPort { get; set; }
    
    [JsonPropertyName("LastLoggedInUser")]
    public User? LastLoggedInUser { get; set; }

    private static readonly string ConfigPath = Path.Combine(AppData.DataPath, "config.json");
    
    
    
    /// <summary>
    /// Loads the application configuration from the config.json file. If the file does not exist, it creates a default configuration and saves it.
    /// If an error occurs during loading, it logs the error and returns a default configuration.
    /// </summary>
    /// <returns></returns>
    public static AppConfig Load()
    {
        try
        {
            var result = new AppConfig();
            
            var dirPath = AppData.DataPath;

            if (!Directory.Exists(dirPath))
            {
                Directory.CreateDirectory(dirPath);
            }
            
            if (!File.Exists(ConfigPath))
            {
                result = BuildDefault();
                Save(result);
                return result;
            }
            
            var json = File.ReadAllText(ConfigPath);
            
            var config = JsonSerializer.Deserialize<AppConfig>(json);

            result = config;

            if (config is null)
            {
                result = BuildDefault();
            }
            
            return result;
        }
        catch (Exception e)
        {
            var log = new Message("Failed to load configuration.", DateTime.Now, "ERROR");
            AppLogger.Instance.LogNewMassage(log);
            return BuildDefault();
        }
        
    }
    
    /// <summary>
    /// Saves the application configuration to the config.json file. The API key is encrypted before saving.
    /// </summary>
    /// <param name="config"></param>
    public static void Save(AppConfig config)
    {
        try
        {
            var configToSave = new AppConfig()
            {
                ServerUrl = config.ServerUrl,
                ServerPort = config.ServerPort,
                LastLoggedInUser = config.LastLoggedInUser
            };
            
            var json = JsonSerializer.Serialize(configToSave, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(ConfigPath, json);
        }
        catch (Exception e)
        {
            var log = new Message("Failed to save configuration.", DateTime.Now, "ERROR");
            AppLogger.Instance.LogNewMassage(log);
        }
    }

    /// <summary>
    /// Builds a default application configuration with predefined server settings and API key. The last logged-in user is set to null.
    /// </summary>
    /// <returns></returns>
    public static AppConfig BuildDefault()
    {
        var result = new AppConfig()
        {
            ServerUrl = "http://127.0.0.1",
            ServerPort = "8765",
            LastLoggedInUser = null 
        };
        
        return result;
    }
}