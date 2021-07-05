# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

from pathlib import Path
from unittest.mock import patch

import pytest

import blackbench
from blackbench import Target

from .utils import PAINT_TASK, fast_run, needs_black


def test_run_custom_help(run_cmd):
    """A smoke test that verifies the custom help class won't crash :p"""
    result = run_cmd(["run", "--help"])
    assert not result.exit_code


@pytest.mark.parametrize("task", blackbench.AVAILABLE_TASKS.keys())
@needs_black
def test_provided_tasks(task: str, tmp_path: Path, tmp_result: Path, run_cmd):
    # All of this complexity is to speed up the test up by avoiding unnecessary targets.
    tiny = tmp_path / "super-tiny.py"
    tiny.write_text("a = 1 + 2 + 3", "utf8")
    cmd = ["run", str(tmp_result), "--task", task, "--targets", "micro"]
    if task.startswith("format"):
        cmd.extend(["--format-config", "is_pyi=True"])

    # fmt: off
    with \
        patch("subprocess.run", fast_run), \
        patch("blackbench.MICRO_TARGETS_DIR", tmp_path) \
    :
        result = run_cmd(cmd)
    # fmt: on

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output


@pytest.mark.parametrize(
    "target",
    [*blackbench.get_provided_targets(True), *blackbench.get_provided_targets(False)],
    ids=lambda t: t.name,
)
def test_provided_targets(tmp_result: Path, run_cmd, target: Target, capsys):
    benchmark = PAINT_TASK.create_benchmark(target)
    # fmt: off
    with \
        patch("subprocess.run", fast_run), \
        blackbench.utils.managed_workdir() as workdir \
    :
        results, errored = blackbench.run_suite([benchmark], [], workdir)
    # fmt: on
    assert results and not errored
    captured = capsys.readouterr()
    assert "ERROR" not in captured.out and "WARNING" not in captured.out


def test_no_duplicated_id():
    targets = [
        *blackbench.get_provided_targets(micro=False),
        *blackbench.get_provided_targets(micro=True),
    ]
    names = [t.name for t in targets]
    names.extend(blackbench.AVAILABLE_TASKS.keys())
    if len(set(names)) != len(names):  # pragma: no cover
        pytest.fail(
            "At least one task / target ID isn't unique,"
            " check the output of `blackbench info` for duplicated IDs"
        )
