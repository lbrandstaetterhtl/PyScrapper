using PyScrapperDesktopApp.Models;

namespace PyScrapperDesktopApp.Tests.Models;

public class MassageTests
{
    [Fact]
    public void Constructor_SetsPropertiesCorrectly()
    {
        var text = "Test message";
        var timestamp = new DateTime(2025, 1, 15, 10, 30, 0);
        var type = "INFO";

        var massage = new Massage(text, timestamp, type);

        Assert.Equal(text, massage.Text);
        Assert.Equal(timestamp, massage.Timestamp);
        Assert.Equal(type, massage.Type);
    }

    [Theory]
    [InlineData("INFO")]
    [InlineData("WARNING")]
    [InlineData("ERROR")]
    public void Constructor_DifferentTypes_SetsTypeCorrectly(string type)
    {
        var massage = new Massage("some text", DateTime.Now, type);

        Assert.Equal(type, massage.Type);
    }

    [Fact]
    public void Constructor_EmptyText_IsAllowed()
    {
        var massage = new Massage("", DateTime.Now, "INFO");

        Assert.Equal("", massage.Text);
    }

    [Fact]
    public void Constructor_NullText_IsAllowed()
    {
        var massage = new Massage(null!, DateTime.Now, "INFO");

        Assert.Null(massage.Text);
    }
}

