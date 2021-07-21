"""
A benchmarking suite for Black, the Python code formatter.
"""

__version__ = "21.6.dev1"

import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import click
import pyperf

from blackbench import resources
from blackbench.clickhacks import CustomHelpCommand
from blackbench.resources import FormatTask, Target, Task
from blackbench.utils import err, log, managed_workdir, warn

THIS_DIR = Path(__file__).parent


# ============ #
# Benchmarking #
# ============ #


class Benchmark:
    def __init__(self, task: Task, target: Target) -> None:
        self.name = f"[{task.name}]-[{target.name}]"
        self.code = task.create_benchmark_script(self.name, target)
        self.micro = target.micro


def run_suite(
    benchmarks: List[Benchmark], pyperf_args: Sequence[str], workdir: Path
) -> Tuple[Optional[pyperf.BenchmarkSuite], bool]:
    results: List[pyperf.Benchmark] = []
    errored = False
    for i, bm in enumerate(benchmarks, start=1):
        log(f"Running `{bm.name}` benchmark ({i}/{len(benchmarks)})")
        script = workdir / f"{i}.py"
        script.write_text(bm.code, encoding="utf8")
        result_file = workdir / f"{i}.json"

        cmd = [sys.executable, str(script), "--output", str(result_file), *pyperf_args]
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


# ============================ #
# Command / CLI implementation #
# ============================ #


class TaskType(click.ParamType):
    name = "task"

    def convert(
        self,
        value: Union[str, Task],
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> Task:
        if isinstance(value, Task):
            return value

        try:
            task = resources.tasks[value.casefold()]
        except KeyError:
            choices_str = ", ".join(resources.tasks.keys())
            self.fail(f"{value} is not one of {choices_str}")

        assert ctx is not None
        if isinstance(task, FormatTask):
            custom_mode = ctx.params["format_config"] or ""
            task = replace(task, custom_mode=custom_mode)

        return task

    def get_metavar(self, param: click.Parameter) -> str:
        return "[" + "|".join(resources.tasks.keys()) + "]"


class TargetSpecifierType(click.ParamType):
    name = "target"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> str:
        normalized = value.casefold()
        if normalized in ("all", "normal", "micro"):
            return normalized

        self.fail(
            f"'{normalized}' is not one of the target groups (micro, normal, and all)"
            " nor the ID of a specific target (run 'blackbench info' for a list)."
        )

    def get_metavar(self, param: click.Parameter) -> str:
        return "[$target-id|micro|normal|all]"


@click.group(context_settings=dict(help_option_names=["-h", "--help"], max_content_width=90))
@click.version_option(
    __version__, package_name=__file__, message="%(prog)s %(version)s, from %(package)s"
)
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    A benchmarking suite for Black, the Python code formatter.

    Now this isn't your typical collection of benchmarks. Blackbench is really a
    collection of targets and task templates. Benchmarks are generated on the fly
    using the task's template as the base and the targets as the profiling data.
    Blackbench comes with pre-curated tasks and targets, allowing for easy and complete
    benchmarking of Black and equally easy performance comparisons.

    Under the hood, blackbench uses pyperf for the actual benchmarking, hence why the
    benchmarking results are in JSON. It's standard pyperf output and it's expected that
    the data analysis is performed using pyperf directly.

    Have fun benchmarking!
    """


@main.command("run", short_help="Run benchmarks and dump results.", cls=CustomHelpCommand)
@click.argument(
    "dump_path",
    metavar="result-filepath",
    type=click.Path(
        file_okay=True, dir_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
)
@click.argument("pyperf-args", metavar="[-- pyperf-args]", nargs=-1, type=click.UNPROCESSED)
@click.option(
    "--task",
    default="format",
    type=TaskType(),
    help="The area of concern to benchmark. [default: format]",
)
@click.option(
    "--targets",
    default="all",
    show_default=True,
    type=TargetSpecifierType(),
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
        " execution time far usually outstrips the drop in result quality. An alias"
        " for `-- --fast`."
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
    pyperf_args: Tuple[str, ...],
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

    if not isinstance(task, FormatTask) and ctx.params["format_config"]:
        warn(
            "Ignoring `--format-config` option since it doesn't make sense"
            f" for the `{task.name}` task."
        )

    pretty_dump_path = str(dump_path.relative_to(os.getcwd()))
    if dump_path.exists():
        warn(f"A file / directory already exists at `{pretty_dump_path}`.")
        click.confirm(
            click.style("[*] Do you want to overwrite and continue?", bold=True), abort=True
        )
    log(f"Will dump results to `{pretty_dump_path}`.")

    selected_targets: List[Target] = []
    if targets.casefold() in ("micro", "all"):
        selected_targets.extend(resources.micro_targets)
    if targets.casefold() in ("normal", "all"):
        selected_targets.extend(resources.normal_targets)
    benchmarks = [Benchmark(task, target) for target in selected_targets]

    prepped_pyperf_args = list(pyperf_args)
    if fast and "--fast" not in pyperf_args:
        prepped_pyperf_args.append("--fast")

    with managed_workdir() as workdir:
        suite_results, errored = run_suite(benchmarks, prepped_pyperf_args, workdir)

    if suite_results:
        suite_results.dump(str(dump_path), replace=True)
        log("Results dumped.")
    else:
        log("No results were collected.")

    end_time = time.perf_counter()
    log(f"Blackbench run finished in {round(end_time - start_time, 3)} seconds.")
    ctx.exit(errored)


@main.command("info")
@click.pass_context
def cmd_info(ctx: click.Context) -> None:
    """Show available targets and tasks."""

    click.secho("Tasks:", bold=True)
    click.echo("  " + ", ".join(resources.tasks.keys()) + "\n")

    click.secho("Normal targets:", bold=True)
    for i, t in enumerate(resources.normal_targets, start=1):
        click.secho(f"  {i}. {t.name}")
    click.echo()

    click.secho("Micro targets:", bold=True)
    for i, t in enumerate(resources.micro_targets, start=1):
        click.secho(f"  {i}. {t.name}")


@main.command("dump")
@click.argument("dump-target", metavar="ID")
@click.pass_context
def cmd_dump(ctx: click.Context, dump_target: str) -> None:
    """Dump the source for a task or target."""
    normalized = dump_target.casefold().strip()
    if task := resources.tasks.get(normalized):
        source = task.source.read_text("utf8")
        click.echo(source, nl=False)
        ctx.exit(0)

    if target := resources.targets.get(normalized):
        source = target.path.read_text("utf8")
        click.echo(source, nl=False)
        ctx.exit(0)

    err(f"No task or target is named '{dump_target}'.")
    ctx.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
