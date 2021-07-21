# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

from pathlib import Path
from unittest.mock import patch

import pytest

from blackbench import Target

from .utils import (
    DATA_DIR,
    PAINT_TASK,
    TEST_MICRO_TARGETS,
    TEST_NORMAL_TARGETS,
    bm_run_mock_helper,
    fast_run,
    get_subprocess_run_commands,
    needs_black,
    replace_resources,
)


def test_info_cmd(run_cmd):
    with replace_resources():
        results = run_cmd("info")
    good = """\
Tasks:
  paint, format

Normal targets:
  1. hello-world.py
  2. goodbye-internet.pyi
  3. i/heard/you/like/nested.py

Micro targets:
  1. tiny.py
"""
    assert results.output == good


def test_dump_cmd_with_task(run_cmd):
    with replace_resources():
        result = run_cmd(["dump", "PaINt"])
    assert not result.exit_code
    assert result.output == PAINT_TASK.template


@pytest.mark.parametrize(
    "target",
    [TEST_NORMAL_TARGETS[0], TEST_MICRO_TARGETS[0]],
    ids=["normal", "micro"],
)
def test_dump_cmd_with_target(target: Target, run_cmd):
    with replace_resources():
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
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
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
    assert output_lines[4] == "[*] Running `[format]-[hello-world.py]` benchmark (2/4)"
    assert output_lines[6] == "[*] Running `[format]-[goodbye-internet.pyi]` benchmark (3/4)"
    assert output_lines[8] == "[*] Running `[format]-[i/heard/you/like/nested.py]` benchmark (4/4)"
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
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
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
    # TODO: check that the right benchmarks were created, instead of this weird logic
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
        result = run_cmd(["run", str(tmp_result), "--targets", "micro"])

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert sub_run.call_count == 1
    good_result = (DATA_DIR / "micro.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


@needs_black
def test_run_cmd_with_normal(tmp_result: Path, run_cmd):
    # TODO: check that the right benchmarks were created, instead of this weird logic
    mock = bm_run_mock_helper(
        [
            DATA_DIR / "normal-goodbye-internet.json",
            DATA_DIR / "normal-hello-world.json",
            DATA_DIR / "normal-nested.json",
        ]
    )
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
        result = run_cmd(["run", str(tmp_result), "--targets", "normal"])

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert sub_run.call_count == 3
    good_result = (DATA_DIR / "normal.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


@needs_black
def test_run_cmd_with_format_config(tmp_result: Path, run_cmd):
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock), replace_resources():
        # fmt: off
        result = run_cmd([
            "run",
            str(tmp_result),
            "--targets", "micro",
            "--task", "format",
            "--format-config", "is_pyi=True",
        ])
        # fmt: on

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    good_result = (DATA_DIR / "micro.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


@needs_black
def test_run_cmd_with_invalid_target(tmp_result: Path, run_cmd):
    invalid_target = Target(DATA_DIR / "invalid-target.py", micro=True)
    # fmt: off
    with \
        patch("blackbench.resources.MICRO_DIR", DATA_DIR), \
        patch("blackbench.resources.micro_targets", [invalid_target]) \
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

    with patch("subprocess.run", fast_run), replace_resources():
        result = run_cmd(
            ["run", str(tmp_result), "--targets", "micro", "--task", "paint"], input="y"
        )
    assert not result.exit_code
    good = """[*] WARNING: A file / directory already exists at `results.json`.
[*] Do you want to overwrite and continue? [y/N]: y
"""
    assert good in result.output
    assert tmp_result.read_text("utf8") != "aaaa"


@needs_black
def test_run_cmd_with_pyperf_args(tmp_result: Path, run_cmd):
    # TODO: maybe check via pyperf results instead of checking subprocess args
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
        # fmt: off
        result = run_cmd([
                "run", str(tmp_result),
                "--targets", "micro",
                "--task", "format",
                "--",
                "--fast",
                "--values", "1",
        ])
        # fmt: on

    command = get_subprocess_run_commands(sub_run)[0]
    assert command[4:] == ["--fast", "--values", "1"]
    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    good_result = (DATA_DIR / "micro.results.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result
