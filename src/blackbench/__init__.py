"""
A benchmarking suite for Black, the Python code formatter.
"""

__version__ = "21.7+dev3"

import os
import subprocess
import sys
import textwrap
import time
from dataclasses import replace
from operator import attrgetter
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

import click
import cloup
import pyperf
from click.shell_completion import CompletionItem
from cloup import HelpFormatter, HelpTheme

from blackbench import resources
from blackbench.resources import FormatTask, Target, Task
from blackbench.utils import err, log, managed_workdir, warn

THIS_DIR = Path(__file__).parent


# ============ #
# Benchmarking #
# ============ #


class Benchmark:
    def __init__(self, task: Task, target: Target) -> None:
        self.name = f"{task.name}-{target.name}"
        self.code = task.create_benchmark_script(self.name, target)
        self.micro = target.micro
        self.target = target
        self.task = task


def run_suite(
    benchmarks: List[Benchmark], pyperf_args: Sequence[str], workdir: Path
) -> Tuple[Optional[pyperf.BenchmarkSuite], bool]:
    results: List[pyperf.Benchmark] = []
    errored = False
    for i, bm in enumerate(benchmarks, start=1):
        bm_type = f"{'micro' if bm.micro else ''}benchmark"
        bm_count = f"({i}/{len(benchmarks)})"
        log(f"Running `{bm.name}` {bm_type} {bm_count}", bold=True)
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
            log(f"Took {round(t1 - t0, 3)} seconds.", bold=True)

            result = pyperf.Benchmark.loads(result_file.read_text(encoding="utf8"))
            results.append(result)
    else:
        if results:
            return pyperf.BenchmarkSuite(results), errored
        else:
            return None, True


# ================= #
# Config validation #
# ================= #


def check_pyperf_args(args: Sequence[str]) -> None:
    benchmark = Path(THIS_DIR, "misc", "dummy-benchmark.py")
    try:
        # fmt: off
        subprocess.run(
            [sys.executable, str(benchmark), "--processes", "1", "--loops", "1", *args],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf8"
        )
        # fmt: on
    except subprocess.CalledProcessError as e:
        err(f"Invalid pyperf arguments: {' '.join(args)}")
        pretty = textwrap.indent(e.stdout.strip(), " " * 4)
        click.secho(pretty)
        sys.exit(2)


def check_mode_config(config: str) -> None:
    import black

    try:
        eval(f"black.FileMode({config})", {"black": black})
    except Exception as e:
        err(f"Invalid black.Mode configuration: {config}")
        pretty = textwrap.indent(f"{e.__class__.__name__}: {e}", " " * 4)
        click.secho(pretty)
        sys.exit(2)


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
            self.fail(f"{value} is not one of {choices_str}.")

        assert ctx is not None
        if isinstance(task, FormatTask):
            custom_mode = ctx.params["format_config"] or ""
            task = replace(task, custom_mode=custom_mode)

        return task

    def get_metavar(self, param: click.Parameter) -> str:  # pragma: no cover
        return "[" + "|".join(resources.tasks.keys()) + "]"

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:  # pragma: no cover
        return [CompletionItem(t.name, help=t.description) for t in resources.tasks.values()]


class TargetSpecifierType(click.ParamType):
    name = "target"

    def convert(
        self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]
    ) -> str:
        normalized = value.casefold()
        if normalized in ("all", "normal", "micro") or normalized in resources.targets.keys():
            return normalized

        self.fail(
            f"'{normalized}' is not one of the target groups (micro, normal, and all)"
            " nor the ID of a specific target (run 'blackbench info' for a list)."
        )

    def get_metavar(self, param: click.Parameter) -> str:  # pragma: no cover
        return "[$target-name|micro|normal|all]"

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:  # pragma: no cover
        items = [CompletionItem(t.name, help=t.description) for t in resources.targets.values()]
        items.extend(CompletionItem(group) for group in ("micro", "normal", "all"))
        return items


def targets_callback(
    ctx: click.Context, param: click.Parameter, specifiers: Tuple[str, ...]
) -> List[Target]:
    selected: List[Target] = []
    for specifier in specifiers:
        if specifier == "micro":
            selected.extend(resources.micro_targets)
        elif specifier == "normal":
            selected.extend(resources.normal_targets)
        elif specifier == "all":
            selected.extend(resources.targets.values())
        else:
            selected.append(resources.targets[specifier])

    selected = list(set(selected))
    return sorted(selected, key=attrgetter("name"))


class ResourceType(click.ParamType):
    """Really basic type that only provides shell completion."""

    def shell_complete(
        self, ctx: click.Context, param: click.Parameter, incomplete: str
    ) -> List[CompletionItem]:  # pragma: no cover
        items = [CompletionItem(t.name, help=t.description) for t in resources.targets.values()]
        items.extend(CompletionItem(t.name, help=t.description) for t in resources.tasks.values())
        return items


@cloup.group(formatter_settings=HelpFormatter.settings(theme=HelpTheme.light(), max_width=85))
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


@main.command(
    "run",
    short_help="Run benchmarks and dump results.",
    formatter_settings=HelpFormatter.settings(
        max_width=85, theme=HelpTheme.light(), col2_min_width=10 * 10
    ),
)
@click.argument(
    "dump_path",
    metavar="result-filepath",
    type=click.Path(
        file_okay=True, dir_okay=False, resolve_path=True, writable=True, path_type=Path
    ),
)
@click.argument("pyperf-args", metavar="[-- pyperf-args]", nargs=-1, type=click.UNPROCESSED)
@cloup.option_group(
    "Benchmark selection & customization",
    click.option(
        "--task",
        default="fmt",
        type=TaskType(),
        help="The area of concern to benchmark.  [default: fmt]",
    ),
    click.option(
        "-t",
        "--targets",
        default=["all"],
        show_default=True,
        multiple=True,
        type=TargetSpecifierType(),
        callback=targets_callback,
        help=(
            "The code files to use as the task's input."
            " Normal targets are real-world code files and therefore lead to data that"
            " more represents real-life scenarios. On the other hand, micro targets "
            " usually are very focused on specific parts of Black."
        ),
    ),
    click.option(
        "--format-config",
        is_eager=True,
        help=(
            "Arguments to pass to black.Mode for format tasks. Must be valid argument"
            ' Python code. For example: "experimental_string_processing=True". The context the'
            " value will be substituted in has the Black package imported."
        ),
    ),
)
@cloup.option_group(
    "Benchmarking parameters",
    click.option(
        "--fast",
        default=False,
        is_flag=True,
        help=(
            "Collect less data values for faster result turnaround, at the price of quality."
            " Although with a tuned system, the reduction in execution time far usually outstrips"
            " the drop in result quality. An alias for `-- --fast`."
        ),
    ),
)
@click.pass_context
def cmd_run(
    ctx: click.Context,
    dump_path: Path,
    pyperf_args: Tuple[str, ...],
    task: Task,
    targets: List[Target],
    fast: bool,
    format_config: str,
) -> None:
    """
    Run benchmarks and dump results. The produced JSON file can be analyzed with
    pyperf.

    Please note that it's important you take measures to improve benchmark stability via
    system tuning and/or benchmarking parameter tuning (eg. --affinity).
    """
    start_time = time.perf_counter()

    try:
        import black
    except ImportError as e:
        err(f"Black isn't importable in the current environment: {e}")
        ctx.exit(1)

    log(
        f"Versions: blackbench: {__version__}, pyperf: {pyperf.__version__}"
        f", black: {black.__version__}",
        fg="cyan",
    )

    if not isinstance(task, FormatTask) and format_config:
        warn(
            "Ignoring `--format-config` option since it doesn't make sense"
            f" for the `{task.name}` task."
        )
    check_pyperf_args(pyperf_args)
    check_mode_config(format_config)
    log("Checked configuration and everything's all good!")

    if dump_path.exists():
        try:
            pretty_dump_path = dump_path.relative_to(os.getcwd())
        except ValueError:
            pretty_dump_path = dump_path
        warn(f"A file / directory already exists at `{pretty_dump_path}`.")
        click.confirm("[*] Do you want to overwrite and continue?", abort=True)

    benchmarks = [Benchmark(task, target) for target in targets]

    prepped_pyperf_args = list(pyperf_args)
    if fast and "--fast" not in pyperf_args:
        prepped_pyperf_args.append("--fast")

    with managed_workdir() as workdir:
        log("Alright, let's start!", fg="green", bold=True)
        suite_results, errored = run_suite(benchmarks, prepped_pyperf_args, workdir)

    if suite_results:
        suite_results.dump(str(dump_path), replace=True)
        if not errored:
            log("Results dumped.")
        else:
            warn("Results dumped (at least one benchmark is missing due to failure).")
    else:
        err("No results were collected.")

    end_time = time.perf_counter()
    log(f"Blackbench run finished in {end_time - start_time:.3f} seconds.", fg="green", bold=True)
    ctx.exit(errored)


@main.command("info")
@click.pass_context
def cmd_info(ctx: click.Context) -> None:
    """Show available targets and tasks."""

    def print_item(index: int, name: str, desc: str, lines: Optional[int] = None) -> None:
        assert desc, "tasks / targets should have a non-empty description"
        lines_str = click.style(f"[{lines} lines] ", fg="cyan") if lines else ""
        prepped_desc = click.style(desc, dim=True)
        click.echo(f"  {i}. {name} {lines_str}- {prepped_desc}")

    click.secho("Tasks:", bold=True)
    for i, task in enumerate(resources.tasks.values(), start=1):
        print_item(i, task.name, task.description)
    click.echo()

    click.secho("Normal targets:", bold=True)
    for i, target in enumerate(resources.normal_targets, start=1):
        line_count = len(target.path.read_text("utf8").splitlines())
        print_item(i, target.name, target.description, line_count)
    click.echo()

    click.secho("Micro targets:", bold=True)
    for i, target in enumerate(resources.micro_targets, start=1):
        line_count = len(target.path.read_text("utf8").splitlines())
        print_item(i, target.name, target.description, line_count)


@main.command("dump")
@click.argument("dump-target", metavar="resource-name", type=ResourceType())
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
