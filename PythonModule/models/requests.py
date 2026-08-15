#Imports
from pydantic import BaseModel, Field
from typing import Optional

import os

import PythonModule.core as core

#Downlaod path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



#Classes
class DownloadRequest(BaseModel):
    provider: str

    urls: list[str]
    
    filenames: list[str]

    download_strategie: core.models.Download.DownloadStrategie = core.models.Download.DownloadStrategie.STREAM

    extra_headers: dict | None = None

    download_path: str = ""
    


class CommandRequest(BaseModel):
    command: str



    

class SearchFilters(BaseModel):
    creator: str = ""
    tags: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    provider: str
    search: str
    top: int = 5
    filters: SearchFilters = Field(default_factory=SearchFilters)

class CreateUserRequest(BaseModel):
    username: str
    password: str

class CreatePlaylistRequest(BaseModel):
    user_identifier: str
    name: str
    description: Optional[str] = None

class CreateDownloadedMediaRequest(BaseModel):
    user_identifier: str
    download_path: str
    downloaded_at: str
    is_playable: bool
    url: str
    media_type: str
    title: str

class CreateSettingsRequest(BaseModel):
    user_identifier: str
    default_download_path: str
    dark_mode_enabled: bool
    scan_folder_on_startup: bool

class CreatePlaylistMediaRequest(BaseModel):
    playlist_identifier: str
    media_identifier: str

class DeletePlaylistMediaRequest(BaseModel):
    playlist_identifier: str
    media_identifier: str
    
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str