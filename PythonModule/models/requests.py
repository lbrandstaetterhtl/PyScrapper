#Imports
from pydantic import BaseModel, Field
from typing import Optional

import os

import PythonModule.core as core

#Download path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



#Classes
class DownloadRequest(BaseModel):
    provider: str

    urls: list[str]
    
    filenames: list[str]

    download_strategie: core.models.Download.DownloadStrategie = core.models.Download.DownloadStrategie.STREAM

    preferred_type : str |None = None

    preferred_file : str |None = None

    extra_headers: dict | None = None

    download_path: str | None = project_root

    auto_convert: bool = False



#Checking if all given arguments are valid
    def model_post_init(self, __context):
        try:
            caller = "[server] DownloadRequest.model_post_init"

            core.general.Validate.general.validateStr(argument_name="provider", string=self.provider, caller=caller)
            core.general.Validate.general.validateListStr(argument_name="urls", liste=self.urls, caller=caller)
            core.general.Validate.general.validateListStr(argument_name="filenames", liste=self.filenames, caller=caller)

            core.general.Validate.general.validateGeneralType(
                argument_name="download_strategie", obj=self.download_strategie, objType=core.models.Download.DownloadStrategie, caller=caller
                )

            if self.preferred_type is not None:
                core.general.Validate.general.validateStr(argument_name="preferred_type", string=self.preferred_type, caller=caller)

            if self.preferred_file is not None:
                core.general.Validate.general.validateStr(argument_name="preferred_file", string=self.preferred_file, caller=caller)

            if self.download_strategie == core.models.Download.DownloadStrategie.LOCAL:
                core.general.Validate.general.validateStr(argument_name="download_path", string=self.download_path, caller=caller)
                core.general.Validate.general.validateBool(boolean=self.auto_convert, argument_name="auto_convert", caller=caller)

                if not (
                    os.path.isdir(self.download_path)
                    and os.access(self.download_path, os.W_OK)
                ):
                    raise core.models.errors.ArgumentError(
                        argument="download_path",
                        wanted_type="path to valid folder that is accessible",
                        caller=caller
                    )
                os.makedirs(self.download_path, exist_ok=True)


            if len(self.urls) != len(self.filenames):
                raise core.models.errors.ArgumentErrorCompare(
                    argument_list=["urls", "filenames"],
                    reason=f"Length of urls and filenames wasn't the same.\nLength urls: {len(self.urls)}\nLength filenames: {len(self.filenames)}",
                    caller=caller
                )
#Raising as ValueError so FastAPI will give back error 422
        except Exception as e:
            raise ValueError(e)
        

        


    


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
    apikey: str

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
    apikey: str

class PlaylistModel(BaseModel):
    Identifier: str
    Name: str
    Description: Optional[str] = None

class MediaModel(BaseModel):
    Identifier: str
    Url: str
    MediaType: str
    DownloadedAt: str
    DownloadPath: str
    IsPlayable: bool
    Title: str

class PlaylistMediaModel(BaseModel):
    PlaylistIdentifier: str
    MediaIdentifier: str
    Position: int

class SettingsModel(BaseModel):
    Identifier: str
    DownloadPath: str
    DarkModeEnabled: bool
    ScanFolderOnStartup: bool

class SaveUserDataRequest(BaseModel):
    user_identifier: str
    playlists: list[PlaylistModel]
    medias: list[MediaModel]
    playlist_medias: list[PlaylistMediaModel]
    setting: SettingsModel