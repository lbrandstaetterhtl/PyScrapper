from pydantic import BaseModel, Field
from typing import Optional

import os

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