"""
Resources needed by blackbench (i.e. task and target definitions).
"""

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from blackbench.utils import _gen_python_files

THIS_DIR = Path(__file__).parent
NORMAL_DIR = THIS_DIR / "normal-targets"
MICRO_DIR = THIS_DIR / "micro-targets"
TASK_DIR = THIS_DIR / "task-templates"


@dataclass(frozen=True)
class Target:
    path: Path
    micro: bool
    description: str = ""

    @property
    def name(self) -> str:
        base = MICRO_DIR if self.micro else NORMAL_DIR
        return self.path.relative_to(base).with_suffix("").as_posix()


@dataclass
class Task:
    name: str
    source: Path
    description: str

    @cached_property
    def template(self) -> str:
        return self.source.read_text("utf8")

    def create_benchmark_script(self, name: str, target: Target) -> str:
        return self.template.format(name=name, target=str(target.path))


@dataclass
class FormatTask(Task):
    custom_mode: str = ""

    def create_benchmark_script(self, name: str, target: Target) -> str:
        return self.template.format(name=name, target=str(target.path), mode=self.custom_mode)


_flit_files = [
    *_gen_python_files(NORMAL_DIR / "flit"),
    *_gen_python_files(NORMAL_DIR / "flit_core"),
]
_targets = [
    *[
        Target(path, micro=False, description=f"Black source code from 21.6b0 (#{n})")
        for n, path in enumerate(_gen_python_files(NORMAL_DIR / "black"), start=1)
    ],
    *[
        Target(path, micro=False, description=f"Flit source code from 3.2.0 (#{n})")
        for n, path in enumerate(_flit_files, start=1)
    ],
    Target(MICRO_DIR / "dict-literal.py", micro=True, description="A long dictionary literal"),
    Target(
        MICRO_DIR / "comments.py",
        micro=True,
        description="Code that uses a lot of (maybe special) comments",
    ),
    Target(MICRO_DIR / "list-literal.py", micro=True, description="A long list literal"),
    Target(
        MICRO_DIR / "nested.py",
        micro=True,
        description="Nested functions, literals, if statements ... all the nested!",
    ),
    Target(
        MICRO_DIR / "strings-list.py",
        micro=True,
        description="A list containing 100s of sometimes comma separated strings",
    ),
]
targets = {t.name: t for t in _targets}
normal_targets = [t for t in targets.values() if not t.micro]
micro_targets = [t for t in targets.values() if t.micro]

_tasks = [
    FormatTask(
        "fmt",
        TASK_DIR / "format-template.py",
        description="Standard Black run although safety checks will *always* run",
    ),
    FormatTask(
        "fmt-fast",
        TASK_DIR / "format-fast-template.py",
        description="Standard Black run but safety checks are *disabled*",
    ),
    Task("parse", TASK_DIR / "parse-template.py", description="Only do blib2to3 parsing"),
]
tasks = {task.name: task for task in _tasks}
