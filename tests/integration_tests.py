# mypy: disallow_untyped_defs=False
# mypy: disallow_incomplete_defs=False

# NOTE: I know that there's actually a mix of integration and functional
# tests in here but I don't need one more test file right now.

from pathlib import Path
from typing import List, Set
from unittest.mock import patch

import pytest

import blackbench
from blackbench import Target

from .utils import (
    DATA_DIR,
    PAINT_TASK,
    TEST_MICRO_PATH,
    TEST_MICRO_TARGETS,
    TEST_NORMAL_TARGETS,
    bm_run_mock_helper,
    fast_run,
    get_subprocess_run_commands,
    log_benchmarks,
    replace_resources,
)


def test_info_cmd(run_cmd):
    with replace_resources():
        results = run_cmd("info")
    good = """\
Tasks:
  1. paint - A joke about Black @ichard26 makes too much
  2. fmt - basically normal fmt but copied for stability

Normal targets:
  1. hello-world [74 lines] - a
  2. goodbye-internet [57 lines] - b
  3. i/heard/you/like/nested [1 lines] - c

Micro targets:
  1. tiny [1 lines] - very tiny indeed
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


def test_run_cmd(tmp_result: Path, run_cmd):
    # TODO: make these run command tests less brittle
    # TODO: improve result data checks to be more flexible
    # fmt: off
    mock = bm_run_mock_helper([
        DATA_DIR / "micro-tiny.json",
        DATA_DIR / "normal-goodbye-internet.json",
        DATA_DIR / "normal-hello-world.json",
        DATA_DIR / "normal-nested.json",
    ])
    # fmt: on
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
    assert len(output_lines) == 14
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert output_lines[0].startswith("[*] Versions: blackbench: ")
    assert output_lines[1].startswith("[*] Created temporary workdir at `")
    assert output_lines[2] == "[*] Alright, let's start!"
    assert output_lines[3] == "[*] Running `fmt-goodbye-internet` benchmark (1/4)"
    assert output_lines[5] == "[*] Running `fmt-hello-world` benchmark (2/4)"
    assert output_lines[7] == "[*] Running `fmt-i/heard/you/like/nested` benchmark (3/4)"
    assert output_lines[9] == "[*] Running `fmt-tiny` microbenchmark (4/4)"
    assert output_lines[-3] == "[*] Cleaning up."
    assert output_lines[-2] == "[*] Results dumped."
    assert output_lines[-1].startswith("[*] Blackbench run finished in")


def test_run_cmd_with_fast(tmp_result: Path, run_cmd):
    # fmt: off
    mock = bm_run_mock_helper([
        DATA_DIR / "micro-tiny.json",
        DATA_DIR / "normal-goodbye-internet.json",
        DATA_DIR / "normal-hello-world.json",
        DATA_DIR / "normal-nested.json",
    ])
    # fmt: on
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
        result = run_cmd(["run", str(tmp_result), "--fast"])
    commands = get_subprocess_run_commands(sub_run)

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    assert sub_run.call_count == 4
    for cmd in commands:
        assert len(cmd) == 5
        assert "--fast" in cmd


@pytest.mark.parametrize("group", ["micro", "normal"])
def test_run_cmd_with_nonall_group(tmp_result: Path, run_cmd, group: str):
    with replace_resources(), log_benchmarks(mock=True) as logged:
        run_cmd(["run", str(tmp_result), "--targets", group])

    if group == "normal":
        assert all(not bm.target.micro for bm in logged)
    else:
        assert all(bm.target.micro for bm in logged)


# fmt: off
@pytest.mark.parametrize("values, expected", [
    (["hello-world"], {"hello-world"}),
    (["micro", "hello-world"], {"tiny", "hello-world"}),
    (["micro", "micro"], {"tiny"}),
])
# fmt: on
def test_run_cmd_targets_opt(run_cmd, tmp_result: Path, values: List[str], expected: Set[str]):
    with replace_resources():
        with log_benchmarks(mock=True) as logged:
            run_cmd(["run", str(tmp_result), *[f"-t{v}" for v in values]])
        assert {bm.target.name for bm in logged} == expected


@pytest.mark.parametrize("option", ["targets", "task"])
def test_custom_resource_types_with_invalid(run_cmd, option: str):
    result = run_cmd(["run", f"--{option}", "yeah-no"])
    assert result.exit_code == 2
    assert "Error: Invalid value for" in result.output


def test_run_cmd_with_format_config(tmp_result: Path, run_cmd):
    # TODO: this probably isn't testing much, checking the benchmark code is probably better.
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock), replace_resources():
        # fmt: off
        result = run_cmd([
            "run", str(tmp_result), "-t", "tiny", "--format-config", "is_pyi=True",
        ])
        # fmt: on

    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    good_result = (DATA_DIR / "micro-tiny.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


def test_run_cmd_with_invalid_target(tmp_result: Path, run_cmd):
    invalid_target = Target(TEST_MICRO_PATH / "invalid-target.py", micro=True)
    # fmt: off
    with \
        patch("blackbench.resources.MICRO_DIR", TEST_MICRO_PATH), \
        patch("blackbench.resources.micro_targets", [invalid_target]) \
    :
        result = run_cmd(["run", str(tmp_result), "--targets", "micro"])
    # fmt: on

    assert result.exit_code == 1
    # There's also an error if there's no results to dump.
    assert result.output.count("ERROR") == 2 and "WARNING" not in result.output


def test_run_cmd_with_preexisting_file(tmp_result: Path, run_cmd):
    tmp_result.touch()
    result = run_cmd(["run", str(tmp_result)], input="n")
    assert result.exit_code == 1
    good = """[*] WARNING: A file / directory already exists at `results.json`.
[*] Do you want to overwrite and continue? [y/N]: n
"""
    assert good in result.output


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


def test_run_cmd_with_pyperf_args(tmp_result: Path, run_cmd):
    # TODO: maybe check via pyperf results instead of checking subprocess args
    mock = bm_run_mock_helper([DATA_DIR / "micro-tiny.json"])
    with patch("subprocess.run", wraps=mock) as sub_run, replace_resources():
        # fmt: off
        result = run_cmd([
            "run", str(tmp_result),
            "-t", "tiny",
            "--",
            "--fast",
            "--values", "1",
        ])
        # fmt: on

    command = get_subprocess_run_commands(sub_run)[0]
    assert command[4:] == ["--fast", "--values", "1"]
    assert not result.exit_code
    assert "ERROR" not in result.output and "WARNING" not in result.output
    good_result = (DATA_DIR / "micro-tiny.json").read_text("utf8")
    assert tmp_result.read_text("utf8") == good_result


def test_run_cmd_with_partial_failure(run_cmd, tmp_result: Path) -> None:
    invalid_target = Target(TEST_MICRO_PATH / "invalid-target.py", micro=True)
    with replace_resources(), patch("subprocess.run", fast_run):
        blackbench.resources.targets["invalid-target"] = invalid_target
        blackbench.resources.micro_targets.append(invalid_target)
        result = run_cmd(["run", str(tmp_result), "-t", "tiny", "-t", "invalid-target"])

    assert "ERROR: Failed to run benchmark" in result.output
    assert (
        "WARNING: Results dumped (at least one benchmark is missing due to failure)"
        in result.output
    )
