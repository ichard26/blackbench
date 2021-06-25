import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Generator, List

import click


def log(msg: str, **kwargs: Dict[str, Any]) -> None:
    _kwargs: Dict[str, Any] = {"bold": True}
    _kwargs.update(kwargs)
    click.secho(f"[*] {msg}", **_kwargs)


def warn(msg: str, **kwargs: Dict[str, Any]) -> None:
    _kwargs: Dict[str, Any] = {"fg": "yellow"}
    _kwargs.update(kwargs)
    log(f"WARNING: {msg}", **_kwargs)


def err(msg: str, **kwargs: Dict[str, Any]) -> None:
    _kwargs: Dict[str, Any] = {"fg": "red"}
    _kwargs.update(kwargs)
    log(f"ERROR: {msg}", **_kwargs)


@contextmanager
def managed_workdir() -> Generator[Path, None, None]:
    with TemporaryDirectory(prefix="blackbench-workdir-") as f:
        log(f"Created temporary workdir at `{f}`.")
        try:
            yield Path(f)
        finally:
            log("Cleaning up.")


def _gen_python_files(path: Path) -> List[Path]:
    files = []
    for entry in os.scandir(path):
        entry_path = Path(entry.path)
        if entry_path.suffix in (".py", ".pyi") and entry.is_file():
            files.append(entry_path)
        elif entry.is_dir():
            files.extend(_gen_python_files(entry_path))

    return sorted(files)
