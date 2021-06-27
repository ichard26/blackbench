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

## License

Blackbench: MIT.

Targets based off real code maintain their original license. Please check the directory
containing the target in question for a license file.
