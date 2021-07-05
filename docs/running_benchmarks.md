# Running benchmarks

```{important}
**Pre-requisite:** an installation of Black that's importable in the current environment
(please make sure the task you're using [supports your installed version of Black](labels/task-compatibility)).
```

Running benchmarks is as simple as calling the run command and providing a filepath to
dump results to:

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ blackbench run example.json
[*] Will dump results to `example.json`.
[*] Created temporary workdir at `/tmp/blackbench-workdir-hw781x4m`.
[*] Running `[format]-[strings-list.py]` benchmark (1/1)
.....................
WARNING: the benchmark result may be unstable
* the maximum (75.8 ms) is 50% greater than the mean (50.6 ms)

Try to rerun the benchmark with more runs, values and/or loops.
Run 'python -m pyperf system tune' command to reduce the system jitter.
Use pyperf stats, pyperf dump and pyperf hist to analyze results.
Use --quiet option to hide these warnings.

[format]-[strings-list.py]: Mean +- std dev: 50.6 ms +- 4.1 ms
[*] Took 29.607 seconds.
[*] Cleaning up.
[*] Results dumped.
[*] Blackbench run finished in 29.851 seconds.
```

**Note how there's a "WARNING: the benchmark result may be unstable" line in the
output.** This leads perfectly into the next topic when running benchmarks: stability
and reliability.

(labels/benchmark-stability)=

## Benchmark stability

While blackbench is supposed to be rather easy to use, one must understand the basics of
*stable* benchmarks and their importance. Stable as in the data doesn't vary all of the
place for absolutely no good reason (it's sorta like avoiding flakey tests). Instable
benchmarks don't produce quality data or allow for accurate comparisons.

For a good backgrounder on stable benchmarks I'd recommend Victor Stinner's "My journey
to stable benchmark" series. In particular the
[My journey to stable benchmark, part 1 (system)](https://vstinner.github.io/journey-to-stable-benchmark-system.html)
and
[My journey to stable benchmark, part 3 (average)](https://vstinner.github.io/journey-to-stable-benchmark-average.html)
articles. But in general,
[pyperf has good documentation on tuning your system](https://pyperf.readthedocs.io/en/latest/run_benchmark.html#stable-bench)
to increase benchmark stability.

```{warning}
Note the suggested modifications may not be supported for
your specific environment and also can be annoying to undo (a simple reboot should clear them though).
```

## Task & target selection

By default, all targets will selected (i.e. `--targets all`) with the `format` task. If
you'd like to use a different task and/or use a specific kind of targets, there's
options for that:

`--task`
: Choices are `parse`, `format-fast`, and `format`.

`--targets`
: Choices are `micro`, `normal`, and `all`.

```{seealso}
{doc}`tasks_and_targets`
```

## Blackbench's slowness

Blackbench can be quite slow, this is because pyperf favours rigourness over speed. Many
data points are collected over a series of processes which while does increase the
accuracy it also does increase total benchmark duration.

You can pass `--fast` (which is actually an alias for `-- --fast`) to ask pyperf to
collect less values for faster result turnaround at the price of result quality.
Although with a well tuned system, the reduction in benchmarking time far usually
outstrips the drop in result quality.

## pyperf configuration

pyperf is the library handling the benchmarking work and while its defaults are
excellent (and blackbench just leaves everything on default) sometimes you'll need to
modify the benchmark settings for stability or time requirement reasons. It's possible
to pass all[^1] {py:class}`pyperf.Runner <Runner>`
[CLI options and flags][pyperf-runner-cli].

Just call `blackbench run` with your usual arguments PLUS `--` and then any pyperf
arguments. The `--` is strongly recommended since anything that comes after will be left
unprocessed and won't be treated as options to blackbench.

Examples include:

```
$ blackbench run example.json -- --fast
```

```
$ blackbench run example2.json --task parse -- --affinity 3
```

```
$ blackbench run example3.json --targets micro --format-config "experimental_string_processing=True" -- --values 3 --warmups 2
```

## Benchmark customization

If you're using a format type task, you can use `--format-config` to pass custom
formatting options to Black during benchmarking. The value is substituted into
`black.FileMode({VALUE})` so it must be valid argument Python code. The substitution
context has the Black package imported. For example, passing a custom line length can be
done with `--format-config "line_length=79"`. The generated benchmark script will look
something like this:

```{code-block} python
---
emphasize-lines: 7
---
# In reality, there's a lot of extra supporting code, but it's irrelevant here.

import black

def format_func(code):
    try:
        black.format_file_contents(code, fast=True, mode=black.FileMode(line_length=79))
    except black.NothingChanged:
        pass

runner.bench_func("[example-task]-[example-target]", format_func, code)
```

[^1]: Although note that not all options will play nicely with blackbench's integration with
    pyperf. Examples include `--help`, `--output`, and `--append`.

[pyperf-runner-cli]: https://pyperf.readthedocs.io/en/latest/runner.html
