# core imports

import PythonModule.core as core
from PythonModule.core.network.Session import Session

#Python default imports
from dataclasses import dataclass, field#
from enum import Enum


@dataclass
class ProviderResult:
    url: str 

    download_type: core.models.Download.DownloadType

    extra_headers: dict | None = None

@dataclass
class ProviderResultRequest:
    url: str

    ses: Session

    extra_headers: dict | None = None

    def __post_init__(self):
        core.general.Validate.download.validateHostDefault(
            self.url,caller="ProviderResultRequest.__post_init__"
        )

        core.general.Validate.special.validateSession(
            self.ses, caller="ProviderResultRequest.__post_init__"
        )

        if self.extra_headers:
            core.general.Validate.general.validateDict(
                argument_name="extra_headers", dictionary=self.extra_headers, caller="ProviderResultRequest.__post_init__"
            )


class ProviderNames(Enum):
    YOUTUBE = "youtube"
    BANDCAMP = "bandcamp"
    DEFAULT = "default"
    SOUNDCLOUD = "soundcloud"