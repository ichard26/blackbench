# Analyzing results

Blackbench's output is actually JSON output directly from {pypi}`pyperf`. The JSON file
can be loaded as an instance of {py:class}`pyperf.BenchmarkSuite <BenchmarkSuite>`.
Anyway, this means that all analyzing of the results will happen with pyperf directly.
Don't worry, pyperf should have been installed alongside blackbench.

```{seealso}
[pyperf's excellent analyzing benchmark results docs](https://pyperf.readthedocs.io/en/latest/analyze.html).
```

## Analyzing a single run

### Summary

For a short summary you can use {ref}`pyperf show <show_cmd>` and pass the JSON file.

```console
dev@example:~/blackbench$ pyperf show normal.json
fmt-black/__init__: Mean +- std dev: 1.50 sec +- 0.05 sec
fmt-black/brackets: Mean +- std dev: 479 ms +- 13 ms
fmt-black/comments: Mean +- std dev: 382 ms +- 6 ms
fmt-black/linegen: Mean +- std dev: 1.52 sec +- 0.04 sec
fmt-black/lines: Mean +- std dev: 1.09 sec +- 0.05 sec
fmt-black/mode: Mean +- std dev: 167 ms +- 3 ms
fmt-black/nodes: Mean +- std dev: 1.23 sec +- 0.04 sec
fmt-black/output: Mean +- std dev: 161 ms +- 6 ms
fmt-black/strings: Mean +- std dev: 282 ms +- 8 ms
fmt-comments: Mean +- std dev: 163 ms +- 7 ms
fmt-dict-literal: Mean +- std dev: 227 ms +- 8 ms
fmt-flit/install: Mean +- std dev: 740 ms +- 75 ms
fmt-flit/sdist: Mean +- std dev: 381 ms +- 17 ms
fmt-flit_core/config: Mean +- std dev: 993 ms +- 48 ms
fmt-list-literal: Mean +- std dev: 134 ms +- 4 ms
fmt-nested: Mean +- std dev: 141 ms +- 29 ms
fmt-strings-list: Mean +- std dev: 43.2 ms +- 1.7 ms
```

### Indepth statistics

For more indepth information {ref}`pyperf stats <stats_cmd>` works wonders[^1]:

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf stats example.json
normal
======

Number of benchmarks: 17
Total duration: 2 min 6.1 sec
Start date: 2021-07-26 16:49:33
End date: 2021-07-26 16:52:24

fmt-black/__init__
------------------

Total duration: 18.6 sec
Start date: 2021-07-26 16:49:33
End date: 2021-07-26 16:49:55
Raw value minimum: 1.45 sec
Raw value maximum: 1.56 sec

Number of calibration run: 1
Number of run with values: 5
Total number of run: 6

Number of warmup per run: 1
Number of value per run: 1
Loop iterations per value: 1
Total number of values: 5

Minimum:         1.45 sec
Median +- MAD:   1.49 sec +- 0.04 sec
Mean +- std dev: 1.50 sec +- 0.05 sec
Maximum:         1.56 sec

  0th percentile: 1.45 sec (-4% of the mean) -- minimum
  5th percentile: 1.45 sec (-3% of the mean)
 25th percentile: 1.48 sec (-2% of the mean) -- Q1
 50th percentile: 1.49 sec (-1% of the mean) -- median
 75th percentile: 1.55 sec (+3% of the mean) -- Q3
 95th percentile: 1.55 sec (+3% of the mean)
100th percentile: 1.56 sec (+4% of the mean) -- maximum

Number of outlier (out of 1.38 sec..1.65 sec): 0

fmt-black/brackets
------------------

[snipped ...]
```

### Histogram

{ref}`pyperf hist <hist_cmd>` is rather useful if you're curious to how instable the
data is:

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf hist example.json
fmt-black/__init__
==================

1.52 sec:  3 ######################
1.56 sec:  4 #############################
1.60 sec: 11 ###############################################################################
1.64 sec: 11 ###############################################################################
1.67 sec:  9 #################################################################
1.71 sec:  8 #########################################################
1.75 sec:  5 ####################################
1.79 sec:  3 ######################
1.83 sec:  1 #######
1.87 sec:  0 |
1.91 sec:  1 #######
1.95 sec:  1 #######
1.99 sec:  0 |
2.03 sec:  1 #######
2.06 sec:  0 |
2.10 sec:  0 |
2.14 sec:  0 |
2.18 sec:  0 |
2.22 sec:  0 |
2.26 sec:  0 |
2.30 sec:  0 |
2.34 sec:  0 |
2.38 sec:  1 #######
2.41 sec:  0 |
2.45 sec:  0 |
2.49 sec:  1 #######

fmt-black/brackets
==================

[snipped ...]
```

```{tip}
You can extract the results for a single benchmark via
[`pyperf convert in.json --include-benchmark "${BENCHMARK}" -o out.json`][pyperf-convert]
. Also, most pyperf commands should support `--benchmark` to select only one or a few
benchmarks when passed in a BenchmarkSuite JSON file.
```

```{tip}
If you need the source for either a task or a target for even deeper analysis, you can
call `blackbench dump ${name}`.
```

## Comparing multiple runs

Comparisons between different runs can be done via
{ref}`pyperf compare_to <compare_to_cmd>`. You can pass as many files as you'd wish,
although note the order to ensure the deltas make sense.

```console
dev@example:~/blackbench$ pyperf compare_to normal.json with-esp.json
fmt-black/__init__: Mean +- std dev: [normal] 1.50 sec +- 0.05 sec -> [with-esp] 1.68 sec +- 0.03 sec: 1.12x slower
fmt-black/brackets: Mean +- std dev: [normal] 479 ms +- 13 ms -> [with-esp] 515 ms +- 11 ms: 1.07x slower
fmt-black/comments: Mean +- std dev: [normal] 382 ms +- 6 ms -> [with-esp] 400 ms +- 11 ms: 1.05x slower
fmt-black/mode: Mean +- std dev: [normal] 167 ms +- 3 ms -> [with-esp] 175 ms +- 5 ms: 1.05x slower
fmt-black/strings: Mean +- std dev: [normal] 282 ms +- 8 ms -> [with-esp] 298 ms +- 6 ms: 1.06x slower
fmt-dict-literal: Mean +- std dev: [normal] 227 ms +- 8 ms -> [with-esp] 244 ms +- 6 ms: 1.08x slower
fmt-list-literal: Mean +- std dev: [normal] 134 ms +- 4 ms -> [with-esp] 156 ms +- 19 ms: 1.17x slower
fmt-strings-list: Mean +- std dev: [normal] 43.2 ms +- 1.7 ms -> [with-esp] 184 ms +- 4 ms: 4.25x slower

Benchmark hidden because not significant (9): fmt-black/linegen, fmt-black/lines, fmt-black/nodes, fmt-black/output, fmt-comments, fmt-flit/install, fmt-flit/sdist, fmt-flit_core/config, fmt-nested

Geometric mean: 1.12x slower
```

Note how pyperf determines whether two samples differ significantly (using a Student’s
two-sample, two-tailed t-test with alpha equals to 0.95). This helps out a lot by
ignoring non-meaningful differences, but there's more to know! Getting stable numbers is
really hard, so there's a possibility "significant" results are still just noise (or are
actual results, but are so small to be meaningless). In this case applying a cutoff
might be a good idea (you can ask pyperf to do this for you via `--min-speed`). What
cutoff to use depends on what benchmarks you ran - a 5% perf improvement on a
microbenchmark most likely isn't as meaningful as one on a (normal) benchmark, AND how
stable your data was (if you system was very noisy then maybe the great results you're
seeing aren't actually real ...). One final tip is to use the "Geometric mean" value, if
you see a general speedup by 10%, then it seems likely you got a nice win on your hands!

### Table view

While's compare_to's default format is neatly compact, it can be a bit hard to parse.
Using `--table` fixes that:

```console
dev@example:~/blackbench$ pyperf compare_to normal.json with-esp.json --table
+--------------------+----------+------------------------+
| Benchmark          | normal   | with-esp               |
+====================+==========+========================+
| fmt-black/__init__ | 1.50 sec | 1.68 sec: 1.12x slower |
+--------------------+----------+------------------------+
| fmt-black/brackets | 479 ms   | 515 ms: 1.07x slower   |
+--------------------+----------+------------------------+
| fmt-black/comments | 382 ms   | 400 ms: 1.05x slower   |
+--------------------+----------+------------------------+
| fmt-black/mode     | 167 ms   | 175 ms: 1.05x slower   |
+--------------------+----------+------------------------+
| fmt-black/strings  | 282 ms   | 298 ms: 1.06x slower   |
+--------------------+----------+------------------------+
| fmt-dict-literal   | 227 ms   | 244 ms: 1.08x slower   |
+--------------------+----------+------------------------+
| fmt-list-literal   | 134 ms   | 156 ms: 1.17x slower   |
+--------------------+----------+------------------------+
| fmt-strings-list   | 43.2 ms  | 184 ms: 4.25x slower   |
+--------------------+----------+------------------------+
| Geometric mean     | (ref)    | 1.12x slower           |
+--------------------+----------+------------------------+

Benchmark hidden because not significant (9): fmt-black/linegen, fmt-black/lines, fmt-black/nodes, fmt-black/output, fmt-comments, fmt-flit/install, fmt-flit/sdist, fmt-flit_core/config, fmt-nested
```

```{tip}
Passing the `-G` flag causes compare_to's output to be organized in groups of
faster/slower/not-significant. This usually makes the output more readable.
```

```{todo}
Provide more examples and also improve their quality. Perhaps also add some more
prose and discussion on then using this data to make inferences and conclusions (as
much as that makes this ever closer to some sort of statistics 101 primer).
```

```{todo}
Provide an example demonstrating `pyperf metadata` once blackbench injects useful
metadata.
```

[^1]: I gave up trying to make my hastily gathered (I asked pyperf to collect like only five
    values per benchmark!) data look normal, please don't @ me if your data doesn't look
    like mine :P
