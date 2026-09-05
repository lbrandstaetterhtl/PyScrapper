from enum import Enum

class ProcessDrainType(Enum):
    MANUAL = "manual",
    PRINT = "print",
    CALLBACK = "callback",
    NONE = "none"

class ProcessOutputType(Enum):
    STDOUT = "stdout",
    STDERR = "stderr"