#Core imports
from ..general import Validate
from ..models.errors import TaskFailedError
#Own imports
from . import processes_models

#Python default imports
import asyncio


class AsyncProcessManager():
    def __init__(
            self,
            process_args: list[str],
            stdout_drain_type: processes_models.ProcessDrainType = processes_models.ProcessDrainType.PRINT,
            stderr_drain_type: processes_models.ProcessDrainType = processes_models.ProcessDrainType.PRINT,
            pass_fds: tuple[int, ...] = (),
            process_name: str = ""
            ):

        Validate.general.validateListStr(
            argument_name="process_args",
            liste=process_args,
            caller="[CORE] AsyncProcessManager.__init__"
        )

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
        if process_name:
            Validate.general.validateStr(   
                argument_name="process_name",
                string=process_name,
                caller="[CORE] AsyncProcessManager.__init__"
            )
            self.name = process_name
        else:
            self.name = "AsyncProcessManager-Unknown-Process"


        self.process = None
        self.args = process_args

        self.stdoutDrain = stdout_drain_type
        self.stderrDrain = stderr_drain_type

        self.stdoutDrainTask = None
        self.stderrDrainTask = None


        self.stderrLines = []
        self.stdoutLines = []

        self.passFds = pass_fds





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
    



    async def start(self):

        self.process = await asyncio.create_subprocess_exec(
            *self.args,

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
            pass_fds=self.passFds
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




    async def stop(self):
        if self.process is None:
            return
        
        print(f"[{self.name}] Process will be stopped now and every task cancelled")

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
