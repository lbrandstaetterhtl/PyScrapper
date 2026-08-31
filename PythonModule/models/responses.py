from pydantic import BaseModel, Field
from typing import Optional
import PythonModule.core as core

import os
from dataclasses import dataclass, field




@dataclass
class Resources:
    context: core.models.Download.DownloadContext

    progress_url : str
    download_url: str | None= None
    watch_url : str | None= None
    

    stream_type :str | None= None


#Context-Felder, die nie mit einer Antwort nach aussen gehen
HIDDEN_CONTEXT_FIELDS = (
    "target",
    "download_progress",
    "info"
)


#exclude kennt Mengen- und Dict-Schreibweise, hier wird alles auf Dicts gebracht
def _excludeAsDict(value):
    if isinstance(value, dict):
        return {key: _excludeAsDict(inner) for key, inner in value.items()}

    if isinstance(value, (set, frozenset, list, tuple)):
        return {key: True for key in value}

    return True


#Fuehrt zwei exclude-Angaben zusammen. Ein ganzes Feld schlaegt eine Teilauswahl
def _mergeExclude(first, second):
    if first is None:
        return second

    if second is None:
        return first

    first = _excludeAsDict(first)
    second = _excludeAsDict(second)

    if first is True or second is True:
        return True

    merged = dict(first)

    for key, value in second.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = _mergeExclude(merged[key], value)

        elif merged.get(key) is True or value is True:
            merged[key] = True

        else:
            merged[key] = value

    return merged


class DownloadResponse(BaseModel):
    task_id: str

    resources: list[Resources] = field(
        default_factory=list
    )

#target, download_progress und info werden immer entfernt, egal was der Aufrufer uebergibt
    def model_dump(self, **kwargs):
        hidden = {
            "resources": {
                "__all__": {
                    "context": {
                        name: True for name in HIDDEN_CONTEXT_FIELDS
                    }
                }
            }
        }

        kwargs["exclude"] = _mergeExclude(kwargs.get("exclude"), hidden)

        return super().model_dump(**kwargs)




class MessageResponse(BaseModel):
    message: str

class CreateResponse(BaseModel):
    message: str
    identifier: str

class CreatePlaylistMediaResponse(BaseModel):
    message: str
    position: int

class LoginResponse(BaseModel):
    message: str
    identifier: str

class UserResponse(BaseModel):
    Identifier: str
    Username: str
    CreatedAt: str

class PlaylistResponse(BaseModel):
    Identifier: str
    UserIdentifier: Optional[str] = None
    Name: str
    Description: Optional[str] = None

class DownloadedMediaResponse(BaseModel):
    Identifier: str
    UserIdentifier: str
    Url: Optional[str] = None
    MediaType: str
    DownloadedAt: str
    DownloadPath: str
    IsPlayable: bool
    Title: str

class SettingsResponse(BaseModel):
    Identifier: str
    UserIdentifier: str
    DownloadPath: str
    DarkModeEnabled: bool
    ScanFolderOnStartup: bool

class PlaylistMediaResponse(BaseModel):
    PlaylistIdentifier: str
    MediaIdentifier: str
    Position: int