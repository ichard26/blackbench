# mypy: disallow_untyped_defs=False

from pathlib import Path
from typing import Dict, Optional
from unittest.mock import patch

import click
import pytest

import blackbench

from .utils import (
    DATA_DIR,
    DIR_SEP,
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


def test_gen_python_files():
    target_dir = DATA_DIR / "normal-targets"
    discovered_files = blackbench.utils._gen_python_files(target_dir)
    assert discovered_files == TEST_NORMAL_TARGETS


def test_task_callback():
    good_path = TEST_TASK_TEMPLATES["paint"]
    good = blackbench.Task("paint", good_path.read_text(encoding="utf8"), good_path)
    ctx = FakeContext(params={"format_config": ""})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "paint")
    assert task == good


def test_task_callback_with_custom_config(capsys):
    good_path = TEST_TASK_TEMPLATES["paint"]
    good = blackbench.Task("paint", good_path.read_text(encoding="utf8"), good_path)
    ctx = FakeContext(params={"format_config": "I will cause a warning :p"})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "paint")
    captured = capsys.readouterr()
    assert good == task
    good_out = (
        "[*] WARNING: Ignoring `--format-config` option since it doesn't make sense"
        " for the `paint` task.\n"
    )
    assert captured.out == good_out


def test_task_callback_with_format_task():
    good_path = TEST_TASK_TEMPLATES["format"]
    good = blackbench.FormatTask(
        "format", good_path.read_text(encoding="utf8"), good_path
    )
    ctx = FakeContext(params={"format_config": ""})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "format")
    assert task == good


def test_task_callback_with_format_task_and_custom_config():
    good_path = TEST_TASK_TEMPLATES["format"]
    good = blackbench.FormatTask(
        "format", good_path.read_text(encoding="utf8"), good_path, "is_pyi=True"
    )
    ctx = FakeContext(params={"format_config": "is_pyi=True"})
    with replace_data_files():
        task = blackbench.task_callback(ctx, FakeParameter(), "format")
    assert task == good


@pytest.mark.parametrize("task_name", ["paint", "format"])
def test_task_create_benchmark(task_name: str) -> None:
    good_path = TEST_TASK_TEMPLATES[task_name]
    if task_name == "paint":
        task = blackbench.Task.from_file("paint", good_path)
    else:
        task = blackbench.FormatTask.from_file("format", good_path, "is_pyi=True")
    target = blackbench.Target(TEST_MICRO_PATH / "tiny.py", micro=True)

    with replace_data_files():
        bm = task.create_benchmark(target)

    assert bm.name == f"[{task_name}]-[tiny.py]"
    assert bm.micro
    good_template = (TASKS_DIR / f"{task_name}-template.py").read_text(encoding="utf8")
    if task_name == "paint":
        good_code = good_template.format(
            target=target.path.resolve(),
            name="[paint]-[tiny.py]",
        )
    else:
        good_code = good_template.format(
            target=target.path.resolve(),
            name="[format]-[tiny.py]",
            mode="is_pyi=True",
        )
    assert bm.code == good_code
    assert bm.target_based == target
    assert bm.task_based == task


def test_msg(capsys):
    blackbench.utils.log("i'm a log msg")
    captured = capsys.readouterr()
    assert captured.out == "[*] i'm a log msg\n"


def test_warn(capsys):
    blackbench.utils.warn("i'm a warning msg")
    captured = capsys.readouterr()
    assert captured.out == "[*] WARNING: i'm a warning msg\n"


def test_err(capsys):
    blackbench.utils.err("i'm a error msg!")
    captured = capsys.readouterr()
    assert captured.out == "[*] ERROR: i'm a error msg!\n"


def test_managed_workdir(tmp_path, capsys):
    with patch("tempfile.tempdir", str(tmp_path)):
        with blackbench.utils.managed_workdir():
            entries = list(tmp_path.iterdir())
            assert len(entries) == 1
            assert entries[0].name.startswith("blackbench")
            captured = capsys.readouterr()
            assert (
                f"[*] Created temporary workdir at `{tmp_path!s}{DIR_SEP}blackbench"
                in captured.out
            )

        assert not len(list(tmp_path.iterdir()))
        captured = capsys.readouterr()
        assert captured.out == "[*] Cleaning up.\n"


@pytest.mark.parametrize(
    "micro, tpath", [(True, TEST_MICRO_PATH), (False, TEST_NORMAL_PATH)]
)
def test_target_name(micro: bool, tpath: Path) -> None:
    with replace_data_files():
        t = blackbench.Target(tpath / "ello.py", micro=micro)
        assert t.name == "ello.py"


def test_get_provided_targets_normal():
    with replace_data_files():
        targets = blackbench.get_provided_targets(micro=False)
        expected = [blackbench.Target(p, False) for p in TEST_NORMAL_TARGETS]
        assert targets == expected


def test_get_provided_targets_micro():
    with replace_data_files():
        targets = blackbench.get_provided_targets(micro=True)
        expected = [blackbench.Target(p, True) for p in TEST_MICRO_TARGETS]
        assert targets == expected
