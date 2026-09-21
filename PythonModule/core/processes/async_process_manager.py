#Core imports
from ..general import Validate
from ..models.errors import TaskFailedError, ArgumentError
#Own imports
from . import processes_models

#Python default imports
import asyncio
import os
import uuid

#Pip imports
if os.name == "nt":
    import win32pipe, win32file



async def writeFd(fd: int, data: bytes):
    offset = 0

    while offset < len(data):
        written = await asyncio.to_thread(
            os.write,
            fd,
            data[offset:],
        )

        if written <= 0:
            raise BrokenPipeError(
                "FFmpeg input pipe was closed"
            )

        offset += written




class AsyncProcessManager():
    def __init__(
            self,
            stdout_drain_type: processes_models.ProcessDrainType = processes_models.ProcessDrainType.PRINT,
            stderr_drain_type: processes_models.ProcessDrainType = processes_models.ProcessDrainType.PRINT,
            process_name: str = "",
            input_count: int = 0
            ):


        Validate.general.validateGeneralType(
            argument_name="stdout_drain_type",
            obj=stdout_drain_type,
            objType=processes_models.ProcessDrainType,
            caller="[CORE] AsyncProcessManager.__init__"
        )

        Validate.general.validateGeneralType(
            argument_name="stderr_drain_type",
            obj=stderr_drain_type,
            objType=processes_models.ProcessDrainType,
            caller="[CORE] AsyncProcessManager.__init__"
        )

        Validate.general.validateInt(
            argument_name="input_count",
            integer=input_count,
            caller="[CORE] AsyncProcessManager.__init__"
        )

        Validate.general.validateStr(   
            argument_name="process_name",
            string=process_name,
            caller="[CORE] AsyncProcessManager.__init__"
        )

        uid = uuid.uuid4()
        self.passFds = ()
        self.inputPipes: list[processes_models.InputPipe] = []

        for p in range(input_count):
            pipe = self._generateInputPipe(
                index=p,
                uid = uid,
                operating_system=os.name
                )
            if pipe.os_type == "posix":
                self.passFds += (pipe.read_fd,)
            self.inputPipes.append(pipe)

        
        
        self.name = process_name
        

        self.process = None


        self.stdoutDrain = stdout_drain_type
        self.stderrDrain = stderr_drain_type

        self.stdoutDrainTask = None
        self.stderrDrainTask = None


        self.stderrLines = []
        self.stdoutLines = []


        





    def _generateInputPipe(
            self,
            index: int,
            uid: int, 
            operating_system: str
            ):
        if operating_system == "posix":

            readFd, writeFd = os.pipe()
            return processes_models.InputPipe(
                pipe_index=index,
                read_fd=readFd,
                write_fd=writeFd,
                pipe_name=f"pipe:{readFd}",
                os_type=operating_system,
                
            )
        
        elif operating_system == "nt":
            pipeName: str = rf"\\.\pipe\pyscrapper_input_{uid}_{index}"
            handle = win32pipe.CreateNamedPipe(
                pipeName,
                win32pipe.PIPE_ACCESS_OUTBOUND,
                win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_WAIT,
                1,
                65536,
                65536,
                0,
                None,
            )

            return processes_models.InputPipe(
                pipe_index=index,
                os_type=operating_system,
                handle=handle,
                pipe_name=pipeName
            )
    




    def _getDrainTask(
            self,
            method: processes_models.ProcessDrainType,
            output: processes_models.ProcessOutputType
            ):
        
        if method == processes_models.ProcessDrainType.PRINT:
            return self._printDrain

        
        elif method == processes_models.ProcessDrainType.MANUAL:

            if output == processes_models.ProcessOutputType.STDERR:
                return self.readStderr
            
            elif output == processes_models.ProcessOutputType.STDOUT:
                return self.readStdout







    async def _printDrain(
            self,
            stream: asyncio.StreamReader,
            stream_name: str
            ):

        lines = (
            self.stderrLines
            if stream_name == "STDERR"
            else self.stdoutLines
        )
        
        while True:
            line = await stream.readline()

            if not line:
                break

            text = line.decode(
                errors="replace"
            ).rstrip()

            lines.append(text)

            if len(lines) > 100:
                lines.pop(0)

            print(
                f"[{self.name}] [{stream_name}] {text}"
            )
        





    async def _readStream(
            self,
            stream: asyncio.StreamReader,
            chunk_size: int
    ):
        data = await stream.read(
                    chunk_size
                )

    #If there is no data, 0 will be given back and True for "hey this stream has ended"
        if not data:
            return b"", True
        
        return data, False
        





    async def readStdout(
            self,
            chunk_size: int = 8192
            ):
        
        if self.stdoutDrain != processes_models.ProcessDrainType.MANUAL:
            raise TaskFailedError(
                task=f"[{self.name}].readStdout",
                reason="Flag for reading stdout was never set",
                extraMessages=[
                    f"Given drain type was {self.stdoutDrain}"
                ],
                caller=f"[{self.name}].readStdout"
            )

        try:
            Validate.general.validateInt(
                argument_name="chunk_size",
                integer=chunk_size,
                caller=f"[{self.name}].readStdout"
            )

        except Exception as e:
            print(f"[{self.name}] WARNING: given chunk_size is invalid, using default size of 8192. Error message: {e}")
            chunk_size = 8192

        return await self._readStream(self.process.stdout, chunk_size)

        

    



    async def readStderr(
            self,
            chunk_size: int = 8192
            ):
        
        if self.stderrDrain != processes_models.ProcessDrainType.MANUAL:
            raise TaskFailedError(
                task=f"[{self.name}].readStderr",
                reason="Flag for reading Stderr was never set",
                extraMessages=[
                    f"Given drain type was {self.stderrDrain}"
                ],
                caller=f"[{self.name}].readStderr"
            )


        try:
            Validate.general.validateInt(
                argument_name="chunk_size",
                integer=chunk_size,
                caller=f"[{self.name}].readStderr"
            )
        except Exception as e:
            print(f"[{self.name}] WARNING: given chunk_size is invalid, using default size of 8192. Error message: {e}")
            chunk_size = 8192

        return await self._readStream(self.process.stderr, chunk_size)
    







    async def start(
            self,
            process_args: list[str],
            ):

        print("LOOP:", type(asyncio.get_running_loop()))
        print("ARGS:", process_args)
        print("OS:", os.name)

        Validate.general.validateListStr(
            argument_name="process_args",
            liste=process_args,
            caller="[CORE] AsyncProcessManager.__init__"
        )
        
        self.process = await asyncio.create_subprocess_exec(
            *process_args,

            stdin=asyncio.subprocess.PIPE,

            stdout=(
                asyncio.subprocess.PIPE
                if self.stdoutDrain != processes_models.ProcessDrainType.NONE
                else None
            ),

            stderr=(
                asyncio.subprocess.PIPE
                if self.stderrDrain != processes_models.ProcessDrainType.NONE
                else None
            ),
            pass_fds=self.passFds if os.name == "posix" else ()
        )



        drainTask = self._getDrainTask(self.stdoutDrain, processes_models.ProcessOutputType.STDOUT)

        if drainTask and drainTask != self.readStdout:
            print(f"[{self.name}] Created drain Task for stdout")
            self.stdoutDrainTask = asyncio.create_task(
                drainTask(self.process.stdout, "STDOUT")
            )
        else:
            print(f"[{self.name}] STDOUT mode is manual. Please regulary call 'readStdout' to access data and to keep the process running")



        drainTask = self._getDrainTask(self.stderrDrain, processes_models.ProcessOutputType.STDERR)

        if drainTask and drainTask != self.readStderr:
            print(f"[{self.name}] Created drain Task for stderr")
            self.stderrDrainTask = asyncio.create_task(
                drainTask(self.process.stderr, "STDERR")
            )
        else:
            print(f"[{self.name}] STDERR mode is manual. Please regulary call 'readStderr' to access data and to keep the process running")



    def getInputName(self, input_index: int) -> str:
        self._checkPipeIndex(
            input_index,
            "getInputName",
        )

        return self.inputPipes[input_index].pipe_name




    async def stop(self):
        if self.process is None:
            return
        
        print(f"[{self.name}] Process will be stopped, every task cancelled and all pipes closed")

        for i in range(len(self.inputPipes)):
            await self.closePipe(i)


        if self.process.returncode is None:
            self.process.terminate()

            try:
                await asyncio.wait_for(
                    self.process.wait(),
                    timeout=5,
                )

            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

        tasks = [
            task
            for task in (
                self.stdoutDrainTask,
                self.stderrDrainTask,
            )
            if task is not None
        ]

        for task in tasks:
            if not task.done():
                task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )





    async def wait(self) -> int:
        return await self.process.wait()



    def _checkPipeIndex(self, pipe_index: int, call_function: str):
            if not isinstance(pipe_index, int):
                raise ArgumentError(
                    argument="pipe_index",
                    wanted_type="int",
                    obj=pipe_index,
                    caller=f"{self.name} {call_function}"
                )
    
            if pipe_index not in range(len(self.inputPipes)):
                raise ArgumentError(
                    argument="pipe_index",
                    wanted_type=f"valid pipe index from 0 to {len(self.inputPipes) - 1}",
                    obj=pipe_index,
                    caller=f"{self.name} {call_function}",
                )
    
    
    
    
    async def closePipe(
            self,
            pipe_index: int = 0
    ):
        self._checkPipeIndex(pipe_index, "closePipe")

        pipe: processes_models.InputPipe = self.inputPipes[pipe_index]
        if pipe.closed:
            print(f"{self.name} Pipe '{pipe_index}' is already closed")
            return


        if pipe.os_type == "posix":
            if pipe.write_fd is not None:
                
                os.close(pipe.write_fd)
                pipe.write_fd = None

            if pipe.read_fd is not None:
                os.close(pipe.read_fd)
                pipe.read_fd = None
                
            print(f"{self.name} Successfully closed pipe with the index {pipe_index}")
            pipe.closed = True

        elif pipe.os_type == "nt":
            await asyncio.to_thread(
                win32file.CloseHandle,
                pipe.handle
            )
            pipe.connected = False
            pipe.closed = True
        
        
                

    async def writePipe(
            self,
            data: bytes,
            pipe_index: int = 0
    ):
        
        Validate.general.validateGeneralType(
            argument_name="data",
            obj=data,
            objType=bytes,
            caller=f"{self.name} writePipe"
        )


        self._checkPipeIndex(pipe_index, "writePipe")


        pipe: processes_models.InputPipe = self.inputPipes[pipe_index]
        if pipe.closed:
            print(f"{self.name} writePipe: Pipe with the index {pipe_index} is already closed")
            return

        if pipe.os_type == "posix":
            await writeFd(pipe.write_fd, data)

        elif pipe.os_type == "nt":
            if not pipe.connected:
                print(f"{self.name} writePipe: Connected Pipe with the index {pipe_index}")
                await asyncio.to_thread(
                    win32pipe.ConnectNamedPipe,
                    pipe.handle,
                    None
                )
                pipe.connected = True

            await asyncio.to_thread(
                win32file.WriteFile,
                pipe.handle,
                data
            )