# Core imports
from ..general import Validate
from ..models import errors
from ..processes import AsyncProcessManager, ProcessDrainType
from ..network.file import writeFd

#Own imports
from .ffmpeg_models import FFMPEG_FORMAT_MAPPING

#Python default imports
import os
import shutil
from dataclasses import dataclass


class FFmpegProbe():
    def __init__(self):

        
        ffmpegPath = shutil.which("ffmpeg")
        if not ffmpegPath:
            raise errors.FFmpegNotFoundError(
                caller=f"{self.caller} FFmpegMuxer.__init__"
            )
    