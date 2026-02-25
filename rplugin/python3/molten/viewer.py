import os
import tempfile
from contextlib import contextmanager
from queue import Queue
from typing import Generator, IO, List, Optional, Tuple

from pynvim import Nvim
from pynvim.api import Buffer

from molten.images import Canvas
from molten.moltenbuffer import MoltenKernel
from molten.options import MoltenOptions
from molten.outputchunks import Output


class NullRuntime:
    kernel_name: str = "viewer"
    kernel_id: str
    allocated_files: List[str]

    def __init__(self, kernel_id: str):
        self.kernel_id = kernel_id
        self.allocated_files = []

    def is_ready(self) -> bool:
        return True

    def deinit(self) -> None:
        for path in self.allocated_files:
            if os.path.exists(path):
                os.remove(path)

    def interrupt(self) -> None:
        pass

    def restart(self) -> None:
        pass

    def run_code(self, code: str) -> None:
        pass

    def tick(self, output: Optional[Output]) -> bool:
        return False

    def tick_input(self) -> None:
        pass

    @contextmanager
    def _alloc_file(
        self, extension: str, mode: str
    ) -> Generator[Tuple[str, IO[bytes]], None, None]:
        with tempfile.NamedTemporaryFile(
            suffix="." + extension, mode=mode, delete=False
        ) as file:
            path = file.name
            yield path, file
        self.allocated_files.append(path)


class ViewerKernel(MoltenKernel):
    def __init__(
        self,
        nvim: Nvim,
        canvas: Canvas,
        highlight_namespace: int,
        extmark_namespace: int,
        main_buffer: Buffer,
        options: MoltenOptions,
        kernel_id: str,
    ):
        # Don't call super().__init__() — that starts JupyterRuntime
        self.nvim = nvim
        self.canvas = canvas
        self.highlight_namespace = highlight_namespace
        self.extmark_namespace = extmark_namespace
        self.buffers = [main_buffer]

        self._doautocmd("MoltenInitPre")

        self.runtime = NullRuntime(kernel_id)  # type: ignore[assignment]
        self.kernel_id = kernel_id

        self.outputs = {}
        self.current_output = None
        self.queued_outputs = Queue()

        self.selected_cell = None
        self.should_show_floating_win = False
        self.updating_interface = False

        self.options = options

    def tick(self) -> None:
        pass  # no kernel to poll
