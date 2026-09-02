using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using System.Threading;
using System.Threading.Tasks;

namespace PyScrapperDesktopApp.Models;

public class MediaConverter
{
    private  readonly AppLogger _logger = AppLogger.Instance;
    private static readonly Dictionary<string, List<string>> ContainerCodecs = new(StringComparer.OrdinalIgnoreCase)
    {
        { ".mp3",  ["mp3"] },
        { ".m4a",  ["aac", "alac", "ac3"] },
        { ".mp4",  ["aac", "alac", "mp3", "ac3", "eac3", "flac", "opus", "vorbis", "dts"] },
        { ".flac", ["flac"] },
        { ".wav",  ["pcm_s16le", "pcm_s24le", "pcm_f32le", "pcm_u8", "pcm_s32le"] },
        { ".ogg",  ["vorbis", "opus", "flac"] },
        { ".opus", ["opus"] },
        { ".mkv",  ["mp3", "aac", "alac", "flac", "opus", "vorbis", "ac3", "eac3", "mp2",
            "dts", "truehd", "wmav2", "wavpack", "tta",
            "pcm_s16le", "pcm_s24le", "pcm_f32le"] },
        { ".ts",   ["aac", "mp3", "mp2", "ac3", "eac3", "opus", "dts", "truehd"] }
    };

    private static readonly Dictionary<string, string> ContainerEncoders = new(StringComparer.OrdinalIgnoreCase)
    {
        { ".mp3", "libmp3lame -q:a 2" },
        { ".m4a", "aac -b:a 192k" },
        { ".mp4", "aac -b:a 192k" },
        { ".flac", "flac" },
        { ".wav", "pcm_s16le" },
        { ".ogg", "libvorbis -q:a 5" },
        { ".opus", "libopus -b:a 160k" },
        { ".mkv", "aac -b:a 192k" },
        { ".ts", "aac -b:a 192k" }
    };
    
    private static readonly Dictionary<string, List<string>> ContainerVideoCodecs =
        new(StringComparer.OrdinalIgnoreCase)
        {
            { ".mp4", ["h264", "hevc", "mpeg4"] },
            { ".mkv", ["h264", "hevc", "mpeg4", "vp8", "vp9", "mpeg2video"] },
            { ".ts",  ["h264", "hevc", "mpeg2video"] }
        };

    private const string VideoEncoder = "libx264 -crf 23 -preset fast -pix_fmt yuv420p";

    /// <summary>
    /// Returns the ffmpeg codec argument for one stream.
    ///   "copy"  -> stream fits the target container and is copied
    ///   sonst   -> encoder plus quality settings
    ///   null    -> target container is unknown
    /// </summary>
    /// <param name="codec">Codec reported by ffprobe, e.g. "aac".</param>
    /// <param name="streamType">"audio" or "video".</param>
    /// <param name="targetContainer">Target extension including the dot.</param>
    private static string? GetEncoder(string codec, string streamType, string targetContainer)
    {
        targetContainer = targetContainer.ToLowerInvariant();
 
        if (streamType == "video")
        {
            var supportedVideo = ContainerVideoCodecs.GetValueOrDefault(targetContainer);
 
            if (supportedVideo == null)
                return null;
 
            return supportedVideo.Contains(codec, StringComparer.OrdinalIgnoreCase)
                ? "copy"
                : VideoEncoder;
        }
 
        var supportedAudio = ContainerCodecs.GetValueOrDefault(targetContainer);
 
        if (supportedAudio == null)
            return null;
 
        if (supportedAudio.Contains(codec, StringComparer.OrdinalIgnoreCase))
            return "copy";
 
        return ContainerEncoders.GetValueOrDefault(targetContainer);
    }
    
    private static async Task<Dictionary<string, string>> GetFileCodec(string path)
    {
        Dictionary<string, string> codecs = new(StringComparer.OrdinalIgnoreCase);
        var ffprobePath = App.FindExe("ffprobe");

        using Process ffprobe = new Process()
        {
            StartInfo = new ProcessStartInfo()
            {
                FileName = ffprobePath,
                Arguments = $"-v error -show_entries stream=codec_type,codec_name -of json \"{path}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                StandardErrorEncoding = System.Text.Encoding.UTF8,
                StandardOutputEncoding = System.Text.Encoding.UTF8
            }
        };
        
        ffprobe.Start();
        var stdoutTask = ffprobe.StandardOutput.ReadToEndAsync();
        var stderrTask = ffprobe.StandardError.ReadToEndAsync();

        string json    = await stdoutTask;
        string errors  = await stderrTask;
        
        await ffprobe.WaitForExitAsync();
        
        if (ffprobe.ExitCode != 0 || !string.IsNullOrEmpty(errors))
        {
            throw new  Exception(errors);
        }
        
        using var doc = JsonDocument.Parse(json);
        
        if (doc.RootElement.TryGetProperty("streams", out var streams))
        {
            foreach (var stream in streams.EnumerateArray())
            {
                if (stream.TryGetProperty("codec_name", out var name) && stream.TryGetProperty("codec_type", out var type))
                {
                    var codecType = type.GetString();
                    var codecName = name.GetString();
                    
                    codecs.TryAdd(codecType, codecName);
                }
            }
        }
        
        return codecs;
    }

    /// <summary>
    /// Builds the complete ffmpeg argument string for converting a file into the target container.
    /// Decides per stream whether it can be copied or has to be re-encoded.
    /// </summary>
    /// <param name="targetContainer">Target extension, e.g. ".mp3".</param>
    /// <param name="path">Source file.</param>
    /// <exception cref="NotSupportedException">Target container is not supported.</exception>
    /// <exception cref="InvalidOperationException">Source has no audio but the target is an audio format.</exception>
    private static async Task<(string, string)> GetArguments(string targetContainer, string path)
    {
        targetContainer = targetContainer.ToLowerInvariant();
        if (!targetContainer.StartsWith('.'))
            targetContainer = "." + targetContainer;
     
        var codecs = await GetFileCodec(path);
     
        var fileExtension = Path.GetExtension(path).ToLowerInvariant();
     
        var targetType = AppData.ValidMediaTypes!.GetValueOrDefault(targetContainer, "");
     
        if (targetType == "")
            throw new NotSupportedException(
                $"Target container \"{targetContainer}\" is not supported. " +
                $"Possible are: {string.Join(", ", ContainerCodecs.Keys)}");
     
        if (targetType == "audio" && !codecs.ContainsKey("audio"))
            throw new InvalidOperationException(
                "The given file has no audio streams.");
     
        var outputPath = Path.ChangeExtension(path, targetContainer);
     
        var result = $"-hide_banner -nostdin -loglevel error -y -i \"{path}\"";
     
        var audioCopied = false;
        var audioCodec = codecs.GetValueOrDefault("audio", "");
        
        foreach (var streamType in codecs.Keys)
        {
            if (streamType == "video" && targetType == "audio")
            {
                result += " -vn";
                continue;
            }
     
            var selector = streamType switch
            {
                "audio" => "a",
                "video" => "v",
                _ => null
            };
     
            if (selector == null)
                continue;
     
            var encoderArg = GetEncoder(codecs[streamType], streamType, targetContainer);
     
            if (encoderArg == null)
                throw new NotSupportedException(
                    $"The target container \"{targetContainer}\" cant hold {streamType}-stream");
     
            if (streamType == "audio" && encoderArg == "copy")
                audioCopied = true;
     
            result += $" -c:{selector} {encoderArg}";
        }
     
        if (fileExtension == ".ts"
            && (targetContainer == ".mp4" || targetContainer == ".m4a")
            && audioCopied
            && audioCodec.Equals("aac", StringComparison.OrdinalIgnoreCase))
        {
            result += " -bsf:a aac_adtstoasc";
        }
        
        if (targetContainer == ".mp4" || targetContainer == ".m4a")
            result += " -movflags +faststart";
     
        if (targetContainer == ".mp3")
            result += " -id3v2_version 3";
     
        result += " -progress pipe:1 -nostats";
     
        result += $" \"{outputPath}\"";
     
        return (result, outputPath);
    }

    public static async Task<string> Convert(string path, string targetContainer)
    {
        var (args, outputPath) = await GetArguments(targetContainer, path);
        
        using Process ffmpeg = new Process()
        {
            StartInfo = new ProcessStartInfo()
            {
                FileName = App.FindExe("ffmpeg") ?? throw new InvalidOperationException("ffmpeg not found"),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardErrorEncoding = System.Text.Encoding.UTF8,
                StandardOutputEncoding = System.Text.Encoding.UTF8,
                Arguments = args
            }
        };
        
        ffmpeg.Start();
        
        var stdoutTask = ffmpeg.StandardOutput.ReadToEndAsync();
        var stderrTask = ffmpeg.StandardError.ReadToEndAsync();

        var progress = await stdoutTask;
        var errors   = await stderrTask;
        
        await ffmpeg.WaitForExitAsync();

        if (ffmpeg.ExitCode != 0 || !string.IsNullOrEmpty(errors))
        {
            throw new Exception(errors);
        }
        
        return outputPath;
    }
    
}