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
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf show example.json
[format]-[goodbye-internet.pyi]: Mean +- std dev: 1.01 ms +- 0.03 ms
[format]-[hello-world.py]: Mean +- std dev: 97.5 ms +- 4.4 ms
[format]-[i/heard/you/like/nested.py]: Mean +- std dev: 551 us +- 35 us
```

### Indepth statistics

For more indepth information {ref}`pyperf stats <stats_cmd>` works wonders:

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf stats example.json
example
==============

Number of benchmarks: 3
Total duration: 18.6 sec
Start date: 2021-06-20 13:17:52
End date: 2021-06-20 13:19:42

[format]-[goodbye-internet.pyi]
-----------------------------------------------------------------

Total duration: 5.3 sec
Start date: 2021-06-20 13:18:30
End date: 2021-06-20 13:18:38
Raw value minimum: 122 ms
Raw value maximum: 142 ms

Number of calibration run: 1
Number of run with values: 10
Total number of run: 11

Number of warmup per run: 1
Number of value per run: 2
Loop iterations per value: 128
Total number of values: 20

Minimum:         950 us
Median +- MAD:   1.01 ms +- 0.01 ms
Mean +- std dev: 1.01 ms +- 0.03 ms
Maximum:         1.11 ms

  0th percentile: 950 us (-6% of the mean) -- minimum
  5th percentile: 964 us (-4% of the mean)
 25th percentile: 987 us (-2% of the mean) -- Q1
 50th percentile: 1.01 ms (+0% of the mean) -- median
 75th percentile: 1.02 ms (+1% of the mean) -- Q3
 95th percentile: 1.04 ms (+4% of the mean)
100th percentile: 1.11 ms (+10% of the mean) -- maximum

Number of outlier (out of 941 us..1062 us): 1

[format]-[hello-world.py]

[snipped]
```

### Histogram

{ref}`pyperf hist <hist_cmd>` is rather useful if you're curious to how instable the
data is:

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf hist example.json
[format]-[goodbye-internet.pyi]
=================================================================

 944 us: 1 ################
 951 us: 0 |
 957 us: 0 |
 963 us: 3 ###############################################
 970 us: 0 |
 976 us: 1 ################
 982 us: 0 |
 989 us: 2 ################################
 995 us: 1 ################
1.00 ms: 1 ################
1.01 ms: 3 ###############################################
1.01 ms: 5 ###############################################################################
1.02 ms: 0 |
1.03 ms: 0 |
1.03 ms: 2 ################################
1.04 ms: 0 |
1.05 ms: 0 |
1.05 ms: 0 |
1.06 ms: 0 |
1.06 ms: 0 |
1.07 ms: 0 |
1.08 ms: 0 |
1.08 ms: 0 |
1.09 ms: 0 |
1.10 ms: 0 |
1.10 ms: 1 ################

[format]-[hello-world.py]
===========================================================

91.6 ms: 2 ########################################
92.4 ms: 0 |
93.2 ms: 2 ########################################
93.9 ms: 2 ########################################
94.7 ms: 2 ########################################

[snipped]
```

```{tip}
You can extract the results for a single benchmark via
[`pyperf convert in.json --include-benchmark "${BENCHMARK}" -o out.json`](https://pyperf.readthedocs.io/en/latest/cli.html#pyperf-convert). Also, most pyperf commands should support `--benchmark` to select only one or a few benchmarks when passed in a BenchmarkSuite JSON file.
```

```{tip}
If you need the source for either a task or a target for even deeper analysis, you can
call `blackbench dump ${ID}` with ID being the task / target name.
```

## Comparing multiple runs

Comparsions between different runs can be done via
{ref}`pyperf compare_to <compare_to_cmd>`. You can pass as many files as you'd wish,
although note the order to ensure the deltas make sense.

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf compare_to run1.json run2.json
[parse]-[black/strings.py]: Mean +- std dev: [run1] 84.5 ms +- 25.8 ms -> [run2] 217 ms +- 73 ms: 2.57x slower

Benchmark hidden because not significant (1): [parse]-[strings-list.py]

Geometric mean: 1.67x slower
```

### Table view

While's compare_to's default format is neatly compact, it can be a bit hard to parse.
Using `--table` fixes that :)

```console
ichard26@acer-ubuntu:~/programming/oss/blackbench$ pyperf compare_to run1.json run2.json --table
+----------------------------+---------+----------------------+
| Benchmark                  | run1    | run2                 |
+============================+=========+======================+
| [parse]-[black/strings.py] | 84.5 ms | 217 ms: 2.57x slower |
+----------------------------+---------+----------------------+
| Geometric mean             | (ref)   | 1.67x slower         |
+----------------------------+---------+----------------------+

Benchmark hidden because not significant (1): [parse]-[strings-list.py]
```

```{tip}
Passing the `-G` flag causes compare_to's output to be organized in groups of
faster/slower/notsignificant. This usually makes the output more readable.
```

```{todo}
Provide more examples and also improve the quality.
```
