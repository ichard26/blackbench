import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Final, Generator, List
from unittest.mock import Mock, patch

import blackbench

WINDOWS = sys.platform.startswith("win")
DIR_SEP = "\\" if WINDOWS else "/"
THIS_DIR = Path(__file__).parent
DATA_DIR = THIS_DIR / "data"
TASKS_DIR = DATA_DIR / "tasks"

TEST_TASK_TEMPLATES = {
    "paint": DATA_DIR / "tasks" / "paint-template.py",
    "format": DATA_DIR / "tasks" / "format-template.py",
}

TEST_NORMAL_PATH = DATA_DIR / "normal-targets"
TEST_NORMAL_TARGETS = sorted(
    [
        TEST_NORMAL_PATH / "hello-world.py",
        TEST_NORMAL_PATH / "goodbye-internet.pyi",
        TEST_NORMAL_PATH / "i" / "heard" / "you" / "like" / "nested.py",
    ]
)
TEST_MICRO_PATH = DATA_DIR / "micro-targets"
TEST_MICRO_TARGETS = sorted(
    [
        TEST_MICRO_PATH / "tiny.py",
    ]
)

PAINT_TASK = blackbench.Task.from_file("paint", TEST_TASK_TEMPLATES["paint"])

_original_run: Final = subprocess.run


@contextmanager
def replace_data_files() -> Generator[None, None, None]:
    task_patcher = patch("blackbench.TASK_TEMPLATES", TEST_TASK_TEMPLATES)
    normal_targets_patcher = patch("blackbench.NORMAL_TARGETS_DIR", TEST_NORMAL_PATH)
    micro_targets_patcher = patch("blackbench.MICRO_TARGETS_DIR", TEST_MICRO_PATH)
    task_patcher.start()
    normal_targets_patcher.start()
    micro_targets_patcher.start()
    try:
        yield
    finally:
        task_patcher.stop()
        normal_targets_patcher.stop()
        micro_targets_patcher.stop()


def bm_run_mock_helper(mock_results: List[Path]) -> Callable:
    return_index = 0

    def mock(cmd: List[str], *args: Any, **kwargs: Any) -> None:
        nonlocal return_index
        assert "--output" in cmd
        dump_path_index = cmd.index("--output") + 1
        dump_path = Path(cmd[dump_path_index])
        to_dump = mock_results[return_index].read_text("utf8")
        dump_path.write_text(to_dump, "utf8")
        return_index += 1

    return mock


def fast_run(cmd: List[str], *args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
    cmd.extend(["-w", "0", "-l", "1", "-p", "1", "--values", "1"])
    return _original_run(cmd, *args, **kwargs)


def get_subprocess_run_commands(mock: Mock) -> List[List[str]]:
    return [call_args[0][0] for call_args in mock.call_args_list]
