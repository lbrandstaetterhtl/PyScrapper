using System.Collections.ObjectModel;
using System.Linq;
using Avalonia.Controls;
using Avalonia.Controls.Chrome;
using Avalonia.Threading;
using PyScrapperDesktopApp.Models;
using PyScrapperDesktopApp.ViewModels;

namespace PyScrapperDesktopApp.Views;

public partial class FilterWindow : Window
{
    public FilterWindow()
    {
        InitializeComponent();
        TitleBar.Initialize(this);

        var vm = new FilterWindowViewModel();
        DataContext = vm;
        vm.CloseRequested += Close;
        
        MediaTypeList.SelectionChanged += (_, _) =>
        {
            vm.SelectedMediaTypes = new ObservableCollection<string>(
                MediaTypeList.SelectedItems?.Cast<string>() ?? Enumerable.Empty<string>()
            );
        };

        if (AppData.FilterEnabled)
        {
            AppData.DownloadedMedias.Clear();
            foreach (var media in AppData.OriginalDownloadedMedias)
                AppData.AddDownloadedMedia(media);

            vm.SearchQuery = AppData.CurrentMediaFilter.SearchQuery;
            vm.SelectedMediaTypes = AppData.CurrentMediaFilter.MediaTypes;
            vm.StartDate = AppData.CurrentMediaFilter.StartDate;
            vm.EndDate = AppData.CurrentMediaFilter.EndDate;
            vm.IsPlayable = AppData.CurrentMediaFilter.IsPlayable;

            Dispatcher.UIThread.Post(() =>
            {
                MediaTypeList.SelectedItems?.Clear();
                if (AppData.CurrentMediaFilter.MediaTypes != null)
                    foreach (var type in AppData.CurrentMediaFilter.MediaTypes)
                        MediaTypeList.SelectedItems?.Add(type);
            }, DispatcherPriority.Loaded);
        }
    }
}