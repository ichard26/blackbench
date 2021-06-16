import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from unittest.mock import patch

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
