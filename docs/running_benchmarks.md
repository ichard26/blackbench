# Running benchmarks

**Pre-requisite:** an installation of Black that's importable in the current environment
(please make sure the task you're using
[supports your installed version of Black](labels/task-compatibility)).

The simplest way of running benchmarks is to call the run command providing a filepath
to dump results to:

```console
dev@example:~/blackbench$ blackbench run example.json
[*] Versions: blackbench: 21.7.dev2, pyperf: 2.2.0, black: 21.7b0
[*] Created temporary workdir at `/tmp/blackbench-workdir-67vki43p`.
[*] Alright, let's start!
[*] Running `fmt-black/__init__` benchmark (1/17)
.....................
WARNING: the benchmark result may be unstable
* the standard deviation (546 ms) is 30% of the mean (1.84 sec)
* the maximum (4.64 sec) is 153% greater than the mean (1.84 sec)

Try to rerun the benchmark with more runs, values and/or loops.
Run 'python -m pyperf system tune' command to reduce the system jitter.
Use pyperf stats, pyperf dump and pyperf hist to analyze results.
Use --quiet option to hide these warnings.

fmt-black/__init__: Mean +- std dev: 1.84 sec +- 0.55 sec
[*] Took 166.059 seconds.

[snipped ...]

[*] Cleaning up.
[*] Results dumped.
[*] Blackbench run finished in 818.794 seconds.
```

**Note how there's a "WARNING: the benchmark result may be unstable" line in the
output.** This leads perfectly into the next topic when running benchmarks: stability
and reliability.

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

Some concrete advice is to 1) use pyperf's great system tuning features. Not only does
it have the automagicial `pyperf system tune` command, there's the lovely
`pyperf system show` command which emits revelant system information and even some
advice to further tweak your system! 2) Even if you can't isolate a CPU core, always use
CPU pinning via pyperf's `--affinity`. This avoids the noise caused by the worker
process being constantly assigned and reassigned to different CPU cores over time. 3) If
you feel like it, try learning pyperf's benchmark parameters and see what works well for
you (eg. maybe two warmups is better than one for you!).

If you're curious what I, Richard aka @ichard26, do to tune my system in preparation,
here's a summary:

<details>

<summary>Personal tuning steps</summary>

System notes: it's a dual-core running Ubuntu 20.04 LTS :P

- Reboot

- At the boot menu, add the following Linux kernel parameters: `isolcpus=1`,
  `nohz_full=1`, and `rcu_nocbs=1`

- Once booted, run `pyperf system tune`

- Then run `my-custom-script.bash`:

  ```bash
  # This has to be run under a root shell
  echo userspace > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
  echo userspace > /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor
  echo 2100000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed
  echo 2100000 > /sys/devices/system/cpu/cpu1/cpufreq/scaling_setspeed
  echo 2100000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
  echo 2100000 > /sys/devices/system/cpu/cpu1/cpufreq/scaling_min_freq
  echo 2100000 > /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
  echo 2100000 > /sys/devices/system/cpu/cpu1/cpufreq/scaling_max_freq
  echo 1 > /proc/sys/kernel/perf_event_max_sample_rate
  echo "System tuned :D"
  ```

  This exists because my laptop's cooling capacity isn't good enough to handle the
  `performance` scaling governor that `pyperf system tune` sets. Eventually the CPU
  frequency would gradually go down, killing any hope at reliable results. So instead I
  lock the CPU frequency at 2.1 GHz. There's also a perf event config but that's less
  cool :)

- Run `pyperf system show` to verify I haven't missed anything dumb

</details>

## Task & target selection

By default, all targets will selected (i.e. `--targets all`) with the `fmt` task. If
you'd like to use a different task and/or use a specific kind of targets, there's
options for that:

`--task`
: Choices are `parse`, `fmt-fast`, and `fmt`.

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
Although with a well tuned system, the reduction in benchmarking time is well worth the
(not too bad) drop in result quality.

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
# In reality, there's some more supporting code, but it's irrelevant here.

import black

def format_func(code):
    try:
        black.format_file_contents(code, fast=True, mode=black.FileMode(line_length=79))
    except black.NothingChanged:
        pass

runner.bench_func("example-task-example-target", format_func, code)
```

[^1]: Although note that not all options will play nicely with blackbench's integration with
    pyperf. Examples include `--help`, `--output`, and `--append`.

[pyperf-runner-cli]: https://pyperf.readthedocs.io/en/latest/runner.html
