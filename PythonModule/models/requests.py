
#Imports
from pydantic import BaseModel

import os

#Downlaod path
current_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_path)


#Classes
class DownloadRequest(BaseModel):
    provider: str
    url: str
    mediatype: str = ".mp3"
    filename: str
    download_path: str = os.path.join(project_root, "downloads")


class CommandRequest(BaseModel):
    command: str



    

class SearchRequest(BaseModel):
    provider: str
    search: str
    top: int = 5