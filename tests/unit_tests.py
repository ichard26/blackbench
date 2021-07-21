# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

from dataclasses import replace
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import patch

import click
import pytest

import blackbench
from blackbench import Benchmark

from .utils import (
    DIR_SEP,
    PAINT_TASK,
    TASKS_DIR,
    TEST_MICRO_PATH,
    TEST_NORMAL_PATH,
    TEST_TASKS,
    replace_resources,
    run_suite_no_op,
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


def test_TaskType(run_cmd):
    task_type = blackbench.TaskType()
    with replace_resources():
        task = task_type.convert("paint", FakeParameter(), FakeContext())

    assert task == PAINT_TASK


def test_task_callback_custom_config_warning(run_cmd, tmp_result):
    with replace_resources(), run_suite_no_op():
        result = run_cmd(["run", str(tmp_result), "--format-config", "no", "--task", "paint"])
    good_out = (
        "[*] WARNING: Ignoring `--format-config` option since it doesn't make sense"
        " for the `paint` task.\n"
    )
    assert good_out in result.output


@pytest.mark.parametrize("format_config", ["", "is_pyi=True"])
def test_task_callback_with_format_task(format_config: str):
    good = TEST_TASKS["format"]
    good = replace(good, custom_mode=format_config)
    ctx = FakeContext(params={"format_config": format_config})
    with replace_resources():
        task = blackbench.TaskType().convert("format", FakeParameter(), ctx)
    assert task == good


@pytest.mark.parametrize("task_name", ["paint", "format"])
def test_task_create_benchmark(task_name: str) -> None:
    if task_name == "paint":
        task = PAINT_TASK
    else:
        task = replace(TEST_TASKS["format"], custom_mode="is_pyi=True")
    target = blackbench.Target(TEST_MICRO_PATH / "tiny.py", micro=True, description="")

    with replace_resources():
        bm = Benchmark(task, target)

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


def test_managed_workdir(tmp_path, capsys):
    with patch("tempfile.tempdir", str(tmp_path)), pytest.raises(RuntimeError):
        with blackbench.utils.managed_workdir():
            entries = list(tmp_path.iterdir())
            assert len(entries) == 1
            assert entries[0].name.startswith("blackbench")
            captured = capsys.readouterr()
            assert (
                f"[*] Created temporary workdir at `{tmp_path!s}{DIR_SEP}blackbench" in captured.out
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
    with replace_resources():
        t = blackbench.Target(tpath / "ello.py", micro=micro, description="")
        assert t.name == "ello.py"
