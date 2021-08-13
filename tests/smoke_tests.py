# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

from pathlib import Path
from typing import List
from unittest.mock import patch

import black
import pytest

from blackbench import Target, resources

from .utils import fast_run, replace_targets


@pytest.mark.parametrize("task", resources.tasks.keys())
def test_provided_tasks(task: str, tmp_path: Path, tmp_result: Path, run_cmd):
    cmd = ["run", str(tmp_result), "--task", task, "-t", "tiny"]
    if task.startswith("fmt"):
        cmd.extend(["--format-config", "is_pyi=True"])

    with patch("subprocess.run", fast_run), replace_targets():
        result = run_cmd(cmd)

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output


@pytest.mark.parametrize("target", resources.targets.values(), ids=lambda t: t.name)
def test_provided_targets(tmp_result: Path, run_cmd, target: Target):
    # This is basically what the `fmt` task does, but without the huge subprocess overhead from
    # `blackbench.run_suite`. It's not perfect, but smoke tests should be fast afterall. Oh and
    # don't @ me about internal APIs and whatnot, it's fine (take it from a maintainer of black
    # :P). Although seriously please try to avoid using Black's internal APIs as much as possible
    # because their external usages makes maintenance harder :/
    code = target.path.read_text("utf8")
    try:
        black.format_file_contents(code, fast=False, mode=black.FileMode())
    except black.NothingChanged:
        pass


def test_no_duplicated_id():
    names: List[str] = []
    names.extend(resources.targets.keys())
    names.extend(resources.tasks.keys())
    if len(set(names)) != len(names):  # pragma: no cover
        pytest.fail(
            "At least one task / target ID isn't unique,"
            " check the output of `blackbench info` for duplicated IDs"
        )
