import subprocess
import sys
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Final, Generator, Iterator, List, Optional, Tuple
from unittest.mock import Mock, patch

import pyperf
import pytest

from blackbench import FormatTask, Target, Task

NO_BLACK = False
try:
    import black  # noqa: F401
except ImportError:  # pragma: no cover
    NO_BLACK = True

WINDOWS = sys.platform.startswith("win")
DIR_SEP = "\\" if WINDOWS else "/"
THIS_DIR = Path(__file__).parent
DATA_DIR = THIS_DIR / "data"
TASKS_DIR = DATA_DIR / "tasks"

TEST_TASKS = {
    "paint": Task("paint", DATA_DIR / "tasks" / "paint-template.py", description=""),
    "format": FormatTask("format", DATA_DIR / "tasks" / "format-template.py", description=""),
}

TEST_NORMAL_PATH = DATA_DIR / "normal-targets"
TEST_MICRO_PATH = DATA_DIR / "micro-targets"
TEST_TARGETS = {
    "hello-world.py": Target(TEST_NORMAL_PATH / "hello-world.py", micro=False, description=""),
    "goodbye-internet.pyi": Target(
        TEST_NORMAL_PATH / "goodbye-internet.pyi", micro=False, description=""
    ),
    "i/heard/you/like/nested.py": Target(
        TEST_NORMAL_PATH / "i" / "heard" / "you" / "like" / "nested.py", micro=False, description=""
    ),
    "tiny.py": Target(TEST_MICRO_PATH / "tiny.py", micro=True, description=""),
}
TEST_MICRO_TARGETS = [t for t in TEST_TARGETS.values() if t.micro]
TEST_NORMAL_TARGETS = [t for t in TEST_TARGETS.values() if not t.micro]

PAINT_TASK = TEST_TASKS["paint"]

_original_run: Final = subprocess.run


@contextmanager
def replace_resources() -> Generator[None, None, None]:
    task_patcher = patch("blackbench.resources.tasks", TEST_TASKS)
    normal_dir_patcher = patch("blackbench.resources.NORMAL_DIR", TEST_NORMAL_PATH)
    micro_dir_patcher = patch("blackbench.resources.MICRO_DIR", TEST_MICRO_PATH)
    targets_patcher = patch("blackbench.resources.targets", TEST_TARGETS)
    normal_targets_patcher = patch("blackbench.resources.normal_targets", TEST_NORMAL_TARGETS)
    micro_targets_patcher = patch("blackbench.resources.micro_targets", TEST_MICRO_TARGETS)
    task_patcher.start()
    normal_dir_patcher.start()
    micro_dir_patcher.start()
    targets_patcher.start()
    normal_targets_patcher.start()
    micro_targets_patcher.start()
    try:
        yield
    finally:
        task_patcher.stop()
        normal_dir_patcher.stop()
        micro_dir_patcher.stop()
        targets_patcher.stop()
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


@contextmanager
def run_suite_no_op(
    results: Optional[pyperf.BenchmarkSuite] = None, errored: bool = False
) -> Iterator:
    def no_op(*args: Any, **kwargs: Any) -> Tuple[Optional[pyperf.BenchmarkSuite], bool]:
        return results, errored

    with patch("blackbench.run_suite", wraps=no_op):
        yield


def fast_run(cmd: List[str], *args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
    cmd.extend(["-w", "0", "-l", "1", "-p", "1", "--values", "1"])
    return _original_run(cmd, *args, **kwargs)


def get_subprocess_run_commands(mock: Mock) -> List[List[str]]:
    return [call_args[0][0] for call_args in mock.call_args_list]


def needs_black(func: Callable) -> Callable:
    @wraps(func)
    @pytest.mark.skipif(NO_BLACK, reason="can't import black")
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return wrapper  # type: ignore
