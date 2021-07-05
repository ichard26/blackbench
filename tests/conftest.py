import os
from functools import partial
from pathlib import Path
from typing import Callable

import click
import pytest
from click.testing import CliRunner

import blackbench


@pytest.fixture
def tmp_result(tmp_path: Path) -> Path:
    os.chdir(tmp_path)
    return tmp_path / "results.json"


@pytest.fixture
def run_cmd() -> Callable[..., click.testing.Result]:
    runner = CliRunner()
    return partial(runner.invoke, blackbench.main, catch_exceptions=False)
