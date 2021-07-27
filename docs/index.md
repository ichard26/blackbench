# Blackbench

```{toctree}
---
hidden:
---
quickstart
```

```{toctree}
---
caption: User Guide
hidden:
---
tasks_and_targets
running_benchmarks
analyzing_results
```

```{toctree}
---
caption: Development
hidden:
---
contributing
changelog
acknowledgements
GitHub <https://github.com/ichard26/blackbench>
Discord <https://discord.gg/RtVdv86PrH>
```

A benchmarking suite for Black, the Python code formatter. It's intended to help
quantify changes in performance between versions of Black in a robust and repeatable
manner. Especially useful for verifying a patch doesn't introduce performance
regressions.

```{panels}

**Reliable at its core**
^^^
Under the hood, blackbench uses {pypi}`pyperf` to handle the benchmarking
heavylifting. The pyperf toolkit was designed with benchmark stability as
its number one goal. This is transferred to blackbench, *so as long the
system is properly tuned, the results can be safely considered reliable.*
---

**Customizable benchmarks**
^^^
Blackbench is really a
collection of targets and task templates. Benchmarks are generated on the
fly using the task's template as the base and the targets as the profiling
data. Want to benchmark Black with experimental string processing on?
A simple option and you're good to go!
---

**Ready-to-go & complete**
^^^
Blackbench comes with pre-curated tasks and targets, allowing
for simplified yet complete benchmarking of Black. Notably, blackbench
has both normal and micro targets to measure general and specific performance
respectively.
---

**Comparable results**
^^^
Due to the pyperf base, the benchmarking results are in JSON. It's standard
pyperf output and it's expected that the data analysis is performed using pyperf
directly with its excellent analysis features.

```

## Example run

```console
dev@example:~/blackbench$ blackbench run mypyc-opt1.json --fast --task parse --targets micro -- --affinity 1
[*] Versions: blackbench: 21.7.dev2, pyperf: 2.2.0, black: 21.7b0
[*] Created temporary workdir at `/tmp/blackbench-workdir-c5hoese9`.
[*] Alright, let's start!
[*] Running `parse-comments` microbenchmark (1/5)
...........
parse-comments: Mean +- std dev: 34.1 ms +- 1.0 ms
[*] Took 9.876 seconds.
[*] Running `parse-dict-literal` microbenchmark (2/5)
...........
parse-dict-literal: Mean +- std dev: 37.7 ms +- 2.4 ms
[*] Took 10.548 seconds.
[*] Running `parse-list-literal` microbenchmark (3/5)
...........
parse-list-literal: Mean +- std dev: 21.8 ms +- 2.4 ms
[*] Took 11.154 seconds.
[*] Running `parse-nested` microbenchmark (4/5)
...........
parse-nested: Mean +- std dev: 20.5 ms +- 1.2 ms
[*] Took 10.79 seconds.
[*] Running `parse-strings-list` microbenchmark (5/5)
...........
parse-strings-list: Mean +- std dev: 5.71 ms +- 1.09 ms
[*] Took 11.588 seconds.
[*] Cleaning up.
[*] Results dumped.
[*] Blackbench run finished in 54.139 seconds.
```

A breakdown of what's happening here:

- `mypyc-opt1.json`: the filepath to save the results
- `--task parse`: the timing workload is initial blib2to3 parsing
- `--targets micro`: only run microbenchmarks (that perform the selected task)
- `--fast`: collect less values so results are ready sooner
- everything after `--`: arguments passed to the underlying pyperf process

## License

Blackbench: MIT.

Targets based off real code maintain their original license. Please check the directory
containing the target in question for a license file. There's also one task based off
Black's code. Please also check the task templates directory for more information.
