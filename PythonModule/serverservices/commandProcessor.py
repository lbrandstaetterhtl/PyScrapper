from PythonModule.models.exceptions import CommandError
from PythonModule.models.settings import SUPPORTEDCOMMANDS
from datetime import datetime
import asyncio
import os


class CommandProcessor():
    def __init__(
            self,
            command: str,
            logFile: str,
            logQueue: asyncio.Queue,
            quitEvent: asyncio.Event
            
            ):
        if not isinstance(command, str): raise ValueError('command given needs to be a string!')
        
        if not isinstance(logFile, str): raise ValueError('logFile must be an string')
        logPath = os.path.dirname(logFile)
        os.makedirs(logPath, exist_ok=True)
        if not os.path.exists(logPath): raise Exception(f"Can't write into given logFile {logFile} because it doesn't exist")

        if not isinstance(logQueue, asyncio.Queue): raise ValueError('Command queue given must be an asyncio.Queue')

        if not isinstance(quitEvent, asyncio.Event): raise ValueError("Please provide a quitEvent with type 'asyncio.Event'")

        self.command: str = command
        self.logFile:str = logFile
        self.logQueue:asyncio.Queue = logQueue
        self.quitEvent:asyncio.Event = quitEvent

    async def run(self):
        match self.command.lower():
            case "quit":
                
            
                with open(self.logFile, "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    f.write(f"[{str(timestamp)}] " + "[INFO] Server shutting down..." + "\n")

                self.quitEvent.set()
                if os.name == "nt":
                    os._exit(0)
            case _:
                raise CommandError(command=self.command, supported=SUPPORTEDCOMMANDS)