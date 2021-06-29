# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

import os
from functools import partial
from pathlib import Path
from typing import Callable, Dict, List, Optional
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

import blackbench
from blackbench import Target

from .utils import (
    DATA_DIR,
    DIR_SEP,
    PAINT_TASK,
    TASKS_DIR,
    TEST_MICRO_PATH,
    TEST_MICRO_TARGETS,
    TEST_NORMAL_PATH,
    TEST_NORMAL_TARGETS,
    TEST_TASK_TEMPLATES,
    bm_run_mock_helper,
    fast_run,
    get_subprocess_run_commands,
    needs_black,
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


@pytest.fixture
def tmp_result(tmp_path: Path) -> Path:
    os.chdir(tmp_path)
    return tmp_path / "results.json"


@pytest.fixture
def run_cmd() -> Callable[..., click.testing.Result]:
    runner = CliRunner()
    return partial(runner.invoke, blackbench.main, catch_exceptions=False)


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


def test_info_cmd(run_cmd):
    with replace_data_files():
        results = run_cmd("info")
    good = """\
Tasks:
  paint, format

Normal targets:
  1. goodbye-internet.pyi
  2. hello-world.py
  3. i/heard/you/like/nested.py

Micro targets:
  1. tiny.py
"""
    assert results.output == good


def test_dump_cmd_with_task(run_cmd):
    with replace_data_files():
        result = run_cmd(["dump", "PaINt"])
    assert not result.exit_code
    assert result.output == PAINT_TASK.template


@pytest.mark.parametrize(
    "target",
    [Target(TEST_NORMAL_TARGETS[0], False), Target(TEST_MICRO_TARGETS[0], True)],
    ids=["normal", "micro"],
)
def test_dump_cmd_with_target(target: Target, run_cmd):
    with replace_data_files():
        result = run_cmd(["dump", target.name.upper()])
    assert not result.exit_code
    assert result.output == target.path.read_text("utf8")


def test_dump_cmd_with_nonexistant(run_cmd):
    result = run_cmd(["dump", "good-weather"])
    assert result.exit_code == 1
    assert "[*] ERROR: No task or target is named 'good-weather'.\n" == result.output


@needs_black
def test_run_cmd(tmp_result: Path, run_cmd):
    # TODO: make these run command tests less brittle
    # TODO: improve result data checks to be more flexible
    mock = bm_run_mock_helper(
        [
            DATA_DIR / "micro-tiny.json",
            DATA_DIR / "normal-goodbye-internet.json",
            DATA_DIR / "normal-hello-world.json",
            DATA_DIR / "normal-nested.json",
        ]
    )
    with patch("subprocess.run", wraps=mock) as sub_run, replace_data_files():
        result = run_cmd(["run", str(tmp_result)])
    commands = get_subprocess_run_commands(sub_run)

    assert not result.exit_code
    assert sub_run.call_count == 4
    for cmd in commands:
        assert len(cmd) == 4
        assert "--fast" not in cmd
    good_result = (DATA_DIR / "all.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result

    output_lines = result.output.splitlines()
    assert len(output_lines) == 13
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert output_lines[0] == "[*] Will dump results to `results.json`."
    assert output_lines[1].startswith("[*] Created temporary workdir at `")
    assert output_lines[2] == "[*] Running `[format]-[tiny.py]` benchmark (1/4)"
    assert (
        output_lines[4]
        == "[*] Running `[format]-[goodbye-internet.pyi]` benchmark (2/4)"
    )
    assert output_lines[6] == "[*] Running `[format]-[hello-world.py]` benchmark (3/4)"
    assert (
        output_lines[8]
        == "[*] Running `[format]-[i/heard/you/like/nested.py]` benchmark (4/4)"
    )
    assert output_lines[-3] == "[*] Cleaning up."
    assert output_lines[-2] == "[*] Results dumped."
    assert output_lines[-1].startswith("[*] Blackbench run finished in")


@needs_black
def test_run_cmd_with_fast(tmp_result: Path, run_cmd):
    mock = bm_run_mock_helper(
        [
            DATA_DIR / "micro-tiny.json",
            DATA_DIR / "normal-goodbye-internet.json",
            DATA_DIR / "normal-hello-world.json",
            DATA_DIR / "normal-nested.json",
        ]
    )
    with patch("subprocess.run", wraps=mock) as sub_run, replace_data_files():
        result = run_cmd(["run", str(tmp_result), "--fast"])
    commands = get_subprocess_run_commands(sub_run)

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert sub_run.call_count == 4
    for cmd in commands:
        assert len(cmd) == 5
        assert "--fast" in cmd


@needs_black
def test_run_cmd_with_micro(tmp_result: Path, run_cmd):
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock) as sub_run, replace_data_files():
        result = run_cmd(["run", str(tmp_result), "--targets", "micro"])

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert sub_run.call_count == 1
    good_result = (DATA_DIR / "micro.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


@needs_black
def test_run_cmd_with_normal(tmp_result: Path, run_cmd):
    mock = bm_run_mock_helper(
        [
            DATA_DIR / "normal-goodbye-internet.json",
            DATA_DIR / "normal-hello-world.json",
            DATA_DIR / "normal-nested.json",
        ]
    )
    with patch("subprocess.run", wraps=mock) as sub_run, replace_data_files():
        result = run_cmd(["run", str(tmp_result), "--targets", "normal"])

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert sub_run.call_count == 3
    good_result = (DATA_DIR / "normal.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


@needs_black
def test_run_cmd_with_format_config(tmp_result: Path, run_cmd):
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock), replace_data_files():
        result = run_cmd(
            [
                "run",
                str(tmp_result),
                "--targets",
                "micro",
                "--task",
                "format",
                "--format-config",
                "is_pyi=True",
            ]
        )

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    good_result = (DATA_DIR / "micro.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


@needs_black
def test_run_cmd_with_invalid_target(tmp_result: Path, run_cmd):
    mock_return = [Target(DATA_DIR / "invalid-target.py", micro=True)]
    # fmt: off
    with \
        patch("blackbench.get_provided_targets", lambda *args, **kw: mock_return), \
        patch("blackbench.MICRO_TARGETS_DIR", DATA_DIR) \
    :
        result = run_cmd(["run", str(tmp_result), "--targets", "micro"])
    # fmt: on

    assert result.exit_code == 1
    assert result.output.count("ERROR") == 1 and "WARNING" not in result.output


@needs_black
def test_run_cmd_with_preexisting_file(tmp_result: Path, run_cmd):
    tmp_result.touch()
    result = run_cmd(["run", str(tmp_result)], input="n")
    assert result.exit_code == 1
    good = """[*] WARNING: A file / directory already exists at `results.json`.
[*] Do you want to overwrite and continue? [y/N]: n
Aborted!
"""
    assert result.output == good


@needs_black
def test_run_cmd_with_preexisting_file_but_continue(tmp_result: Path, run_cmd):
    tmp_result.write_text("aaaa", "utf8")

    with patch("subprocess.run", fast_run), replace_data_files():
        result = run_cmd(
            ["run", str(tmp_result), "--targets", "micro", "--task", "paint"], input="y"
        )
    assert not result.exit_code
    good = """[*] WARNING: A file / directory already exists at `results.json`.
[*] Do you want to overwrite and continue? [y/N]: y
"""
    assert good in result.output
    assert tmp_result.read_text("utf8") != "aaaa"


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
        # --fast actually overrides the speed improvements fast_run does.
        results, errored = blackbench.run_suite([benchmark], False, workdir)
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
