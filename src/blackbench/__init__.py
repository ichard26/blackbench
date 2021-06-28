"""
A benchmarking suite for Black, the Python code formatter.
"""

__version__ = "21.6.dev1"

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import click
import pyperf

from .utils import _gen_python_files, err, log, managed_workdir, warn

THIS_DIR = Path(__file__).parent
NORMAL_TARGETS_DIR = THIS_DIR / "normal-targets"
MICRO_TARGETS_DIR = THIS_DIR / "micro-targets"
_TASK_TEMPLATES_DIR = THIS_DIR / "task-templates"
AVAILABLE_TASKS = {
    "parse": _TASK_TEMPLATES_DIR / "parse-template.py",
    # TODO: add support for these tasks:
    # "format-fast-no-parse": _TASK_TEMPLATES_DIR / "format-fast-no-parse-template.py",
    # "format-no-parse": _TASK_TEMPLATES_DIR / "format-no-parse-template.py",
    "format-fast": _TASK_TEMPLATES_DIR / "format-fast-template.py",
    "format": _TASK_TEMPLATES_DIR / "format-template.py",
}


@dataclass(frozen=True)
class Benchmark:
    name: str
    micro: bool
    code: str

    target_based: Optional["Target"] = None
    task_based: Optional["Task"] = None


def get_provided_targets(micro: bool) -> List["Target"]:
    search_dir = MICRO_TARGETS_DIR if micro else NORMAL_TARGETS_DIR
    targets = _gen_python_files(search_dir)
    return [Target(t, micro) for t in targets]


@dataclass(frozen=True)
class Task:
    name: str
    template: str
    source: Path

    @classmethod
    def from_file(cls, name: str, filepath: Path) -> "Task":
        with open(filepath, "r", encoding="utf8") as f:
            value = f.read()

        return cls(name, value, source=filepath)

    def create_benchmark(self, target: "Target") -> "Benchmark":
        bm_name = f"[{self.name}]-[{target.name}]"
        bm_code = self._create_benchmark_script(bm_name, target)

        return Benchmark(
            bm_name, target.micro, bm_code, target_based=target, task_based=self
        )

    def _create_benchmark_script(self, name: str, target: "Target") -> str:
        return self.template.format(name=name, target=str(target.path))


@dataclass(frozen=True)
class FormatTask(Task):
    custom_mode: str = ""

    @classmethod
    def from_file(cls, name: str, filepath: Path, custom_mode: str = "") -> "Task":
        with open(filepath, "r", encoding="utf8") as f:
            value = f.read()

        return cls(name, value, source=filepath, custom_mode=custom_mode)

    def _create_benchmark_script(self, name: str, target: "Target") -> str:
        return self.template.format(
            name=name, target=str(target.path), mode=self.custom_mode
        )


def task_callback(ctx: click.Context, param: click.Parameter, value: str) -> Task:
    normalized = value.casefold()
    if normalized not in AVAILABLE_TASKS:
        options = ", ".join([f"'{t}'" for t in AVAILABLE_TASKS])
        raise click.BadParameter(f"'{normalized}' is not one of {options}.")

    format_config = ctx.params["format_config"]
    if normalized.startswith("format"):
        format_config = format_config or ""
        return FormatTask.from_file(
            normalized, AVAILABLE_TASKS[normalized], custom_mode=format_config
        )

    if ctx.params["format_config"]:
        warn(
            "Ignoring `--format-config` option since it doesn't make sense"
            f" for the `{normalized}` task."
        )

    return Task.from_file(normalized, AVAILABLE_TASKS[normalized])


def run_suite(
    benchmarks: List[Benchmark], fast: bool, workdir: Path
) -> Tuple[Optional[pyperf.BenchmarkSuite], bool]:
    results: List[pyperf.Benchmark] = []
    errored = False
    for i, bm in enumerate(benchmarks, start=1):
        log(f"Running `{bm.name}` benchmark ({i}/{len(benchmarks)})")
        script = workdir / f"{i}.py"
        script.write_text(bm.code, encoding="utf8")
        result_file = workdir / f"{i}.json"

        cmd = [sys.executable, str(script), "--output", str(result_file)]
        if fast:
            cmd.append("--fast")
        t0 = time.perf_counter()
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            err("Failed to run benchmark ^^^")
            errored = True
        else:
            t1 = time.perf_counter()
            log(f"Took {round(t1 - t0, 3)} seconds.")

            result = pyperf.Benchmark.loads(result_file.read_text(encoding="utf8"))
            results.append(result)
    else:
        if results:
            return pyperf.BenchmarkSuite(results), errored
        else:
            return None, True


@dataclass(frozen=True)
class Target:
    path: Path
    micro: bool

    @property
    def name(self) -> str:
        if self.micro:
            return self.path.relative_to(MICRO_TARGETS_DIR).as_posix()
        else:
            return self.path.relative_to(NORMAL_TARGETS_DIR).as_posix()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(
    __version__,
    # Very hacky use of package value :P
    package_name=__file__,
    message="%(prog)s %(version)s from %(package)s",
)
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    A benchmarking suite for Black, the Python code formatter.

    Now this isn't your typical collection of benchmarks. Blackbench is really a
    collection of targets and tasks templates. Benchmarks are generated on the fly
    using the task's template as the base and the targets as the profiling data / code.

    Blackbench comes with pre-curated tasks and targets, allowing for easy and complete
    benchmarking of Black and equally easy performance comparisons.

    Under the hood, blackbench uses pyperf for the actual benchmarking, hence why the
    benchmarking results are in JSON. It's standard pyperf output and it's expected that
    the data analysis is performed using pyperf directly.

    Have fun benchmarking!
    """


@main.command("run", short_help="Run benchmarks and dump results.")
@click.argument(
    "dump_path",
    metavar="result-filepath",
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        writable=True,
        path_type=Path,
    ),
)
@click.option(
    "--task",
    metavar=f"[{'|'.join(AVAILABLE_TASKS)}]",
    default="format",
    callback=task_callback,
    show_default=True,
    help=(
        "Should blackbench measure the performance of a typical Black run (format)"
        " or measure something more specific like blib2to3 parsing (parse)?"
    ),
)
@click.option(
    "--targets",
    default="all",
    type=click.Choice(["normal", "micro", "all"], case_sensitive=False),
    show_default=True,
    help=(
        "Which kind(s) of code files should be used as the task's input?"
        " Normal targets are real-world code files and therefore lead to data that"
        " more represents real-life scenarios. Micro targets are code files that "
        " usually are focused on testing performance of a specific area of Black."
    ),
)
@click.option(
    "--fast",
    default=False,
    is_flag=True,
    help=(
        "Collect less values during benchmarking for faster result turnaround, at the"
        " price of result quality. Although with a tuned system, the reduction in"
        " execution time far usually outstrips the drop in result quality."
    ),
    show_default=True,
)
@click.option(
    "--format-config",
    is_eager=True,
    help=(
        "Arguments to pass to black.Mode for format tasks. Must be valid argument"
        " Python code. Ex. `experimental_string_processing=True`. The context the"
        " value will be substituted in has the Black package imported."
    ),
)
@click.pass_context
def cmd_run(
    ctx: click.Context,
    dump_path: Path,
    task: Task,
    targets: str,
    fast: bool,
    format_config: str,
) -> None:
    """
    Run benchmarks and dump results. The produced JSON file can be analyzed with
    pyperf.
    """
    start_time = time.perf_counter()

    try:
        import black  # noqa: F401
    except ImportError:
        err("Black isn't importable in the current environment.")
        ctx.exit(1)

    pretty_dump_path = str(dump_path.relative_to(os.getcwd()))
    if dump_path.exists():
        warn(f"A file / directory already exists at `{pretty_dump_path}`.")
        click.confirm(
            click.style("[*] Do you want to overwrite and continue?", bold=True),
            abort=True,
        )
    log(f"Will dump results to `{pretty_dump_path}`.")

    selected_targets: List[Target] = []
    if targets.casefold() in ("micro", "all"):
        selected_targets.extend(get_provided_targets(micro=True))
    if targets.casefold() in ("normal", "all"):
        selected_targets.extend(get_provided_targets(micro=False))
    benchmarks = [task.create_benchmark(t) for t in selected_targets]

    with managed_workdir() as workdir:
        suite_results, errored = run_suite(benchmarks, fast, workdir)

    if suite_results:
        suite_results.dump(str(dump_path), replace=True)
        log("Results dumped.")
    else:
        log("No results were collected.")

    end_time = time.perf_counter()
    log(f"Blackbench run finished in {round(end_time - start_time, 3)} seconds.")
    ctx.exit(int(errored))


@main.command("info")
@click.pass_context
def cmd_info(ctx: click.Context) -> None:
    """Show available targets and tasks."""

    click.secho("Tasks:", bold=True)
    click.echo("  " + ", ".join(AVAILABLE_TASKS.keys()) + "\n")

    click.secho("Normal targets:", bold=True)
    normal_iter = enumerate(get_provided_targets(False), start=1)
    click.echo("\n".join(f"  {i}. {t.name}" for i, t in normal_iter))
    click.echo()

    click.secho("Micro targets:", bold=True)
    normal_iter = enumerate(get_provided_targets(True), start=1)
    click.echo("\n".join(f"  {i}. {t.name}" for i, t in normal_iter))

    ctx.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
