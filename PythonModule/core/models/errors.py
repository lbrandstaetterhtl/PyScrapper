class ArgumentError(Exception):
    """Raised when an argument is invalid."""
    pass



class RegexSearchError(Exception):
    def __init__(
            self,
            pattern: str,
            searchBlock: str,
            ):
        self.pattern = pattern

        messages = (
            f"RegexSearchError: Pattern was not found.\n"
            f"Pattern: {pattern}\n"
            f"Search Block: {searchBlock}\n"
        )
        super().__init__(messages)



class MergeError(Exception):
    def __init__(
            self,
            videoFile: str,
            audioFile: str,
            
    ):

        messages = (
            f"Could not merge video and audio files because ffmpeg isn't installed.\n",
            f"Video and Audio got saved!",
            f"Video File: {videoFile}\n",
            f"Audio File: {audioFile}\n",
        )
        super().__init__(messages)