# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import patch

import click
import pytest

import blackbench

from .utils import (
    DIR_SEP,
    PAINT_TASK,
    TASKS_DIR,
    TEST_MICRO_PATH,
    TEST_MICRO_TARGETS,
    TEST_NORMAL_PATH,
    TEST_NORMAL_TARGETS,
    TEST_TASK_TEMPLATES,
    replace_data_files,
)


class FakeContext(click.Context):
    """A fake click Context for when calling functions that need it."""

    def __init__(
        self, *, default_map: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> None:
        self.default_map = default_map or {}
        self.params = params or {}


class FakeParameter(click.Parameter):
    """A fake click Parameter for when calling functions that need it."""

    def __init__(self) -> None:
        pass


def test_task_callback():
    ctx = FakeContext(params={"format_config": ""})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "paint")
    assert task == PAINT_TASK


def test_task_callback_with_custom_config(capsys):
    ctx = FakeContext(params={"format_config": "I will cause a warning :p"})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "paint")
    captured = capsys.readouterr()
    assert task == PAINT_TASK
    good_out = (
        "[*] WARNING: Ignoring `--format-config` option since it doesn't make sense"
        " for the `paint` task.\n"
    )
    assert captured.out == good_out


def test_task_callback_with_format_task():
    good_path = TEST_TASK_TEMPLATES["format"]
    good = blackbench.FormatTask.from_file("format", good_path)
    ctx = FakeContext(params={"format_config": ""})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "format")
    assert task == good


def test_task_callback_with_format_task_and_custom_config():
    good_path = TEST_TASK_TEMPLATES["format"]
    good = blackbench.FormatTask.from_file("format", good_path, "is_pyi=True")
    ctx = FakeContext(params={"format_config": "is_pyi=True"})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "format")
    assert task == good


@pytest.mark.parametrize("task_name", ["paint", "format"])
def test_task_create_benchmark(task_name: str) -> None:
    good_path = TEST_TASK_TEMPLATES[task_name]
    if task_name == "paint":
        task = PAINT_TASK
    else:
        task = blackbench.FormatTask.from_file("format", good_path, "is_pyi=True")
    target = blackbench.Target(TEST_MICRO_PATH / "tiny.py", micro=True)

    with replace_data_files():
        bm = task.create_benchmark(target)

    good_name = f"[{task_name}]-[tiny.py]"
    assert bm.name == good_name
    assert bm.micro
    good_template = (TASKS_DIR / f"{task_name}-template.py").read_text(encoding="utf8")
    if task_name == "paint":
        good_code = good_template.format(target=target.path, name=good_name)
    else:
        good_code = good_template.format(
            target=target.path,
            name=good_name,
            mode="is_pyi=True",
        )
    assert bm.code == good_code
    assert bm.target_based == target
    assert bm.task_based == task


def test_managed_workdir(tmp_path, capsys):
    with patch("tempfile.tempdir", str(tmp_path)), pytest.raises(RuntimeError):
        with blackbench.utils.managed_workdir():
            entries = list(tmp_path.iterdir())
            assert len(entries) == 1
            assert entries[0].name.startswith("blackbench")
            captured = capsys.readouterr()
            assert (
                f"[*] Created temporary workdir at `{tmp_path!s}{DIR_SEP}blackbench"
                in captured.out
            )
            raise RuntimeError

    assert not len(list(tmp_path.iterdir()))
    captured = capsys.readouterr()
    assert captured.out == "[*] Cleaning up.\n"


@pytest.mark.parametrize(
    "micro, tpath",
    [(True, TEST_MICRO_PATH), (False, TEST_NORMAL_PATH)],
    ids=["micro", "normal"],
)
def test_target_name(micro: bool, tpath: Path) -> None:
    with replace_data_files():
        t = blackbench.Target(tpath / "ello.py", micro=micro)
        assert t.name == "ello.py"


@pytest.mark.parametrize(
    "micro, good_targets",
    [(True, TEST_MICRO_TARGETS), (False, TEST_NORMAL_TARGETS)],
    ids=["micro", "normal"],
)
def test_get_provided_targets(micro: bool, good_targets: List[Path]):
    with replace_data_files():
        targets = blackbench.get_provided_targets(micro=micro)
        expected = [blackbench.Target(p, micro) for p in good_targets]
        assert targets == expected
