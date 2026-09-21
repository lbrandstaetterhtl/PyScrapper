from enum import Enum
from dataclasses import dataclass
from typing import Any

class ProcessDrainType(Enum):
    MANUAL = "manual",
    PRINT = "print",
    CALLBACK = "callback",
    NONE = "none"

class ProcessOutputType(Enum):
    STDOUT = "stdout",
    STDERR = "stderr"



@dataclass
class InputPipe:

    pipe_index: int
    pipe_name: str

    os_type: str


    read_fd: int | None = None
    write_fd: int | None = None

    handle : Any | None = None
    
    connected: bool = False
    closed: bool = False