using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using Avalonia.Platform.Storage;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// This class contains interfaces for services used in the application, such as file storage and API communication.
/// </summary>
public static class Interfaces
{
    /// <summary>
    /// Interface for a storage service that provides methods for opening file pickers, saving files, and opening folder pickers.
    /// </summary>
    public interface IStorageService
    {
        Task<IReadOnlyList<IStorageFile>> OpenFilePickerAsync(FilePickerOpenOptions options);
        Task<IStorageFile?> SaveFilePickerAsync(FilePickerSaveOptions options);
        Task<IReadOnlyList<IStorageFolder>> OpenFolderPickerAsync(FolderPickerOpenOptions options);
    }
    
    /// <summary>
    /// Interface for an API client that provides methods for sending scrap requests, getting health status, sending search requests, and getting download progress.
    /// </summary>
    public interface IApiClient
    {
        Task<string> SendScrapRequest(DownloadRequestData data);
        Task<HealthResponse> GetHealth(bool logResponse = true);
        Task<List<ApiClient.SearchResultItem>> SendSearchRequest(SearchRequestData data);
        Task<ProgressSuccessResponse> GetDownloadProgress(string id);
    }
    
    /// <summary>
    /// Interface for an application logger that provides methods for logging new messages and debug messages.
    /// </summary>
    public interface IAppLogger
    {
        void LogNewMassage(Massage massage);
        void LogDebugMessage(Massage massage);
    }

    public interface IAppDataService
    {
        ObservableCollection<DownloadedMedia> DownloadedMedias { get; }
        ObservableCollection<Playlist> Playlists { get; }
        Settings Settings { get; }
        
        void AddDownloadedMedia(DownloadedMedia media);
        void RemoveDownloadedMedia(DownloadedMedia media);
        bool MediaAlreadyExists(string filePath);
    }

    public interface IDialogService
    {
        Task ShowAlertAsync(string message);
        Task<bool> ConfirmAsync(string message);
        Task<string?> AskInputAsync(string message);
    }
}