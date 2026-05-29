using System.IO;
using PyScrapperDesktopApp.ViewModels;
using Xunit;

namespace PyScrapperDesktopApp.Tests.ViewModels;

public class CodecConverterWindowViewModelTests
{
    [Fact]
    public void SetOutputPath_GeneratesCorrectPath()
    {
        var inputPath = @"C:\Downloads\test.webm";
        var expectedOutput = @"C:\Downloads\test_converted.mp4";
        
        var actualOutput = CodecConverterWindowViewModel.SetOutputPath(inputPath);
        
        Assert.Equal(expectedOutput, actualOutput);
    }

    [Fact]
    public void SetOutputPath_HandlesEmptyDirectory()
    {
        var inputPath = "test.webm";
        var expectedOutput = "test_converted.mp4";
        
        var actualOutput = CodecConverterWindowViewModel.SetOutputPath(inputPath);
        
        Assert.Equal(expectedOutput, actualOutput);
    }
}

