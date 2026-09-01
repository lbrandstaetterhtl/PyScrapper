_MISSING = object()

class ArgumentErrorCompare(Exception):
    def __init__(
            self,
            argument_list: list[str],
            reason: str,
            caller: str

            ):

        exceptionMessage = (
            f"[ARGUMENT ERROR COMPARE] {caller}:"
            f"Compared arguments: {', '.join(argument_list)}"
            f"Reason: {reason}"
        )


        super().__init__(exceptionMessage)


class ArgumentError(Exception):
    def __init__(
            self,
            argument: str,
            wanted_type: str,
            obj = _MISSING,
            caller: str = "unknown",
            
    ):
        exceptionMessage = (
            f"[ARGUMENT ERROR] {caller}:"
            f"Given argument {argument} to function {caller} is invalid\n"
            f"Argument {argument} must be from type {wanted_type}\n"
        )
        
        if obj is not _MISSING:
            if obj is None:
                exceptionMessage += (
                    "\nGiven object: None"
                    "\nDetermined type: NoneType"
                )
            else:
                exceptionMessage += (
                    f"\nGiven object: {obj!r}"
                    f"\nDetermined type: {type(obj).__name__}"
                )

        super().__init__(exceptionMessage)


class InvalidURLError(Exception):
    def __init__(
            self,
            url: str,
            reasonList: list = [],
            caller: str = "unknown"
    ):
        exceptionMessage = (
            f"[INVALIDURL ERROR] {caller}: Given URL '{url}' is invalid\n"
            f"Invalidating reasons: {', '.join(reasonList)}"
                )
        super().__init__(exceptionMessage)


class RegexSearchError(Exception):
    def __init__(
            self,
            pattern: str,
            searchBlock: str,
            caller: str = "unknown"
            ):
        self.pattern = pattern

        exceptionMessage = (
            f"[RegexSearchError] {caller}: "
            f"Pattern was not found.\n"
            f"Pattern: {pattern}\n"
            f"Search Block: {searchBlock}\n"
        )
        super().__init__(exceptionMessage)



class MergeError(Exception):
    def __init__(
            self,
            videoFile: str,
            audioFile: str,
            
    ):

        exceptionMessage = (
            f"Could not merge video and audio files because ffmpeg isn't installed.\n",
            f"Video and Audio got saved!",
            f"Video File: {videoFile}\n",
            f"Audio File: {audioFile}\n",
        )
        super().__init__(exceptionMessage)


class TaskFailedError(Exception):
    def __init__(
        self,
        task: str,
        reason: str | None = None,
        extraMessages: list[str] | None = None,
        caller: str = "unknown"
    ):
        exceptionMessage = (
            f"[ERROR] {caller}: "
            f"The following task failed: {task}\n"
        )

        if reason:
            exceptionMessage += (
                f"Failed because of the following reason: {reason}\n"
            )

        if extraMessages:
            exceptionMessage += "Extra messages from function:\n"

            for message in extraMessages:
                exceptionMessage += f"- {message}\n"

        super().__init__(exceptionMessage)




class DRMProtectedMediaError(Exception):
    def __init__(
        self,
        detected_url: str,
        source_url: str | None = None,
        caller: str | None = None,
        drm_type: str | None = None,
    ):
        self.detected_url = detected_url
        self.source_url = source_url
        self.caller = caller
        self.drm_type = drm_type

        parts = ["DRM protected media detected"]

        if drm_type:
            parts.append(f"DRM: {drm_type}")

        parts.append(f"Detected URL: {detected_url}")

        if source_url:
            parts.append(f"Source URL: {source_url}")

        if caller:
            parts.append(f"Caller: {caller}")

        super().__init__(" | ".join(parts))