from dataclasses import dataclass
from enum import Enum


@dataclass
class FFmpegPipe:
    pipe_index: int
    read_pipe: int
    write_pipe: int
    closed : bool = False

@dataclass
class FFmpegCodec:
    codec_name: str
    codec_type: str
    input_index: int = 0

class GetCodecTypes(Enum):
    AUTO = "auto",
    AUDIO = "audio",
    VIDEO = "video"




CONTAINERS = {

    # =========================================================
    # MP4 / MOV FAMILY
    # =========================================================

    "mp4": {
        "ffmpeg_format": "mp4",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        # Conservative policy:
        # codecs we are willing to stream-copy into this container
        "allowed_codecs": {
            "video": {
                "h264",
                "hevc",
                "av1",
                "mpeg4",
                "vp9"
            },
            "audio": {
                "aac",
                "mp3",
                "ac3",
                "eac3",
                "alac",
            },
        },

        "default_encoders": {
            "video": "libx264",
            "audio": "aac",
        },

        "extra_output_args": [
            "-movflags",
            "+frag_keyframe+empty_moov+default_base_moof",
        ],

        # Only apply these when that codec is actually copied.
        "copy_codec_args": {
            "aac": [
                "-bsf:a",
                "aac_adtstoasc",
            ],
        },
    },


    "m4v": {
        "ffmpeg_format": "mp4",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "h264",
                "hevc",
                "av1",
            },
            "audio": {
                "aac",
                "mp3",
                "ac3",
                "eac3",
                "alac",
            },
        },

        "default_encoders": {
            "video": "libx264",
            "audio": "aac",
        },

        "extra_output_args": [
            "-movflags",
            "+frag_keyframe+empty_moov+default_base_moof",
        ],

        "copy_codec_args": {
            "aac": [
                "-bsf:a",
                "aac_adtstoasc",
            ],
        },
    },


    "m4a": {
        "ffmpeg_format": "mp4",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "aac",
                "alac",
                "mp3",
                "ac3",
                "eac3",
            },
        },

        "default_encoders": {
            "audio": "aac",
        },

        "extra_output_args": [
            "-vn",
            "-movflags",
            "+frag_keyframe+empty_moov+default_base_moof",
        ],

        "copy_codec_args": {
            "aac": [
                "-bsf:a",
                "aac_adtstoasc",
            ],
        },
    },


    "mov": {
        "ffmpeg_format": "mov",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "h264",
                "hevc",
                "mpeg4",
                "prores",
                "mjpeg",
            },
            "audio": {
                "aac",
                "mp3",
                "pcm_s16le",
                "pcm_s24le",
                "alac",
                "ac3",
            },
        },

        "default_encoders": {
            "video": "libx264",
            "audio": "aac",
        },

        "extra_output_args": [
            "-movflags",
            "+frag_keyframe+empty_moov+default_base_moof",
        ],

        "copy_codec_args": {
            "aac": [
                "-bsf:a",
                "aac_adtstoasc",
            ],
        },
    },


    # =========================================================
    # MATROSKA / WEBM
    # =========================================================

    "mkv": {
        "ffmpeg_format": "matroska",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        # MKV is extremely flexible.
        "allowed_codecs": {
            "video": {
                "h264",
                "hevc",
                "vp8",
                "vp9",
                "av1",
                "mpeg4",
                "mpeg2video",
                "mpeg1video",
                "theora",
                "prores",
                "mjpeg",
            },
            "audio": {
                #"aac",
                "mp3",
                "opus",
                "vorbis",
                "flac",
                "ac3",
                "eac3",
                "dts",
                "truehd",
                "alac",
                "pcm_s16le",
                "pcm_s24le",
            },
        },

        "default_encoders": {
            "video": "libx264",
            "audio": "aac",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    "webm": {
        "ffmpeg_format": "webm",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "vp8",
                "vp9",
                "av1",
            },
            "audio": {
                "opus",
                "vorbis",
            },
        },

        "default_encoders": {
            "video": "libvpx-vp9",
            "audio": "libopus",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    # =========================================================
    # MPEG
    # =========================================================

    "ts": {
        "ffmpeg_format": "mpegts",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "h264",
                "hevc",
                "mpeg2video",
                "mpeg1video",
            },
            "audio": {
                "aac",
                "mp2",
                "mp3",
                "ac3",
                "eac3",
            },
        },

        "default_encoders": {
            "video": "libx264",
            "audio": "aac",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    "mpeg": {
        "ffmpeg_format": "mpeg",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "mpeg1video",
                "mpeg2video",
            },
            "audio": {
                "mp2",
                "mp3",
            },
        },

        "default_encoders": {
            "video": "mpeg2video",
            "audio": "mp2",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    "mpg": {
        "ffmpeg_format": "mpeg",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "mpeg1video",
                "mpeg2video",
            },
            "audio": {
                "mp2",
                "mp3",
            },
        },

        "default_encoders": {
            "video": "mpeg2video",
            "audio": "mp2",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    # =========================================================
    # AVI / ASF
    # =========================================================

    "avi": {
        "ffmpeg_format": "avi",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "mpeg4",
                "mjpeg",
                "h264",
            },
            "audio": {
                "mp3",
                "ac3",
                "pcm_s16le",
            },
        },

        "default_encoders": {
            "video": "mpeg4",
            "audio": "mp3",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    "wmv": {
        "ffmpeg_format": "asf",

        "allowed_codec_types": {
            "video",
            "audio",
        },

        "allowed_codecs": {
            "video": {
                "wmv1",
                "wmv2",
                "wmv3",
                "vc1",
            },
            "audio": {
                "wmav1",
                "wmav2",
                "mp3",
                "ac3",
            },
        },

        "default_encoders": {
            "video": "wmv2",
            "audio": "wmav2",
        },

        "extra_output_args": [],

        "copy_codec_args": {},
    },


    # =========================================================
    # AUDIO ONLY
    # =========================================================

    "mp3": {
        "ffmpeg_format": "mp3",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "mp3",
            },
        },

        "default_encoders": {
            "audio": "libmp3lame",
        },

        "extra_output_args": [
            "-vn",
        ],

        "copy_codec_args": {},
    },


    "aac": {
        "ffmpeg_format": "adts",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "aac",
            },
        },

        "default_encoders": {
            "audio": "aac",
        },

        "extra_output_args": [
            "-vn",
        ],

        "copy_codec_args": {},
    },


    "flac": {
        "ffmpeg_format": "flac",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "flac",
            },
        },

        "default_encoders": {
            "audio": "flac",
        },

        "extra_output_args": [
            "-vn",
        ],

        "copy_codec_args": {},
    },


    "wav": {
        "ffmpeg_format": "wav",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "pcm_s16le",
                "pcm_s24le",
                "pcm_s32le",
                "pcm_f32le",
                "pcm_f64le",
            },
        },

        "default_encoders": {
            "audio": "pcm_s16le",
        },

        "extra_output_args": [
            "-vn",
        ],

        "copy_codec_args": {},
    },


    "ogg": {
        "ffmpeg_format": "ogg",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "vorbis",
                "opus",
                "flac",
            },
        },

        "default_encoders": {
            "audio": "libopus",
        },

        "extra_output_args": [
            "-vn",
        ],

        "copy_codec_args": {},
    },


    "opus": {
        "ffmpeg_format": "opus",

        "allowed_codec_types": {
            "audio",
        },

        "allowed_codecs": {
            "audio": {
                "opus",
            },
        },

        "default_encoders": {
            "audio": "libopus",
        },

        "extra_output_args": [
            "-vn",
        ],

        "copy_codec_args": {},
    },
}