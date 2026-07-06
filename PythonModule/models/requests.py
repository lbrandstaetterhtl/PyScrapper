#Imports
from pydantic import BaseModel, Field
from typing import Optional

import os

#Downlaod path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


#Classes
class DownloadRequest(BaseModel):
    provider: str
    url: str
    mediatype: str = ".mp3"
    filename: str
    download_path: str = os.path.join(project_root, "downloads")


class CommandRequest(BaseModel):
    command: str



    

class SearchFilters(BaseModel):
    creator: Optional[str] = ""
    tags: Optional[list[str]] = None



class SearchRequest(BaseModel):
    provider: str
    search: str
    top: int = 5
    
    filters: SearchFilters = Field(default_factory=SearchFilters)

class CreateUserRequest(BaseModel):
    username: str
    password: str