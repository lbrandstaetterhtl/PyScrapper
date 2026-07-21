using System.IO;
using Avalonia.Headless.XUnit;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class CodecConverterWindowViewModelTests
{
    [AvaloniaFact]
    public void SetOutputPath_GeneratesCorrectPath()
    {
        var inputPath = @"C:\Downloads\test.webm";
        var expectedOutput = @"C:\Downloads\test_converted.mp4";
        
        var actualOutput = CodecConverterWindowViewModel.SetOutputPath(inputPath);
        
        Assert.Equal(expectedOutput, actualOutput);
    }

    [AvaloniaFact]
    public void SetOutputPath_HandlesEmptyDirectory()
    {
        var inputPath = "test.webm";
        var expectedOutput = "test_converted.mp4";
        
        var actualOutput = CodecConverterWindowViewModel.SetOutputPath(inputPath);
        
        Assert.Equal(expectedOutput, actualOutput);
    }
}

