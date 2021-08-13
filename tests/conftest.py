import os
from pathlib import Path
from typing import Any, Callable, List, Union

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

    def caller(args: Union[str, List[object]] = [], **kwargs: Any) -> click.testing.Result:
        prepped: List[str] = []
        if isinstance(args, list):
            prepped.extend(str(a) for a in args)
        else:
            prepped.append(args)
        return runner.invoke(blackbench.main, prepped, catch_exceptions=True, **kwargs)

    return caller
