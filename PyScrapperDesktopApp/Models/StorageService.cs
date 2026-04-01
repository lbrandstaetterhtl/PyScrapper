using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.Platform.Storage;

namespace PyScrapperDesktopApp.Models;

/// <summary>
/// This class implements the IStorageService interface and provides methods for opening file pickers, saving files, and opening folder pickers using the Avalonia platform storage provider.
/// </summary>
/// <param name="topLevel"></param>
public class StorageService(TopLevel topLevel) : Interfaces.IStorageService
{
    private TopLevel TopLevel => topLevel 
                                 ?? throw new InvalidOperationException("TopLevel is null — StorageService was created before the window was attached to the visual tree.");
    
    /// <summary>
    /// Opens a file picker dialog with the specified options and returns a list of selected storage files.
    /// This method uses the Avalonia platform storage provider to display the file picker and handle user interactions.
    /// </summary>
    /// <param name="options"></param>
    /// <returns></returns>
    public Task<IReadOnlyList<IStorageFile>> OpenFilePickerAsync(FilePickerOpenOptions options)
    {
        return TopLevel.StorageProvider.OpenFilePickerAsync(options);
    }

    /// <summary>
    /// Opens a save file picker dialog with the specified options and returns the selected storage file, or null if the user cancels the operation.
    /// This method uses the Avalonia platform storage provider to display the save file picker and handle user interactions, allowing the user to specify a file name and location for saving a file.
    /// </summary>
    /// <param name="options"></param>
    /// <returns></returns>
    public Task<IStorageFile?> SaveFilePickerAsync(FilePickerSaveOptions options)
    {
        return TopLevel.StorageProvider.SaveFilePickerAsync(options);
    }
    
    /// <summary>
    /// Opens a folder picker dialog with the specified options and returns a list of selected storage folders.
    /// This method uses the Avalonia platform storage provider to display the folder picker and handle user interactions, allowing the user to select one or more folders from the file system.
    /// </summary>
    /// <param name="options"></param>
    /// <returns></returns>
    public Task<IReadOnlyList<IStorageFolder>> OpenFolderPickerAsync(FolderPickerOpenOptions options)
    {
        return TopLevel.StorageProvider.OpenFolderPickerAsync(options);
    }
}