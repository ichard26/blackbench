# Tasks & targets

Blackbench comes with tasks and targets. Tasks represent a specific task Black has do
during formatting, and come with a specific template. Targets are the actual files Black
(or more specifically the task's template / code which calls the relevant Black APIs) is
run against to gauge performance. Together they create benchmarks that are ran using
[pyperf](https://pypi.org/project/pyperf).

Why not just ship ready-to-go benchmark scripts instead? Well, there's a few issues with
that: running static benchmarks limits the available configuration. Want to benchmark
Black with the magic trailing comma disabled? You'd have to edit each benchmark which is
annoying. And even if providing scripts for all of the different possible configurations
was possible, they would be annoying to maintain.

Benchmarks ran by blackbench are named using the task and target they are based off. For
example a benchmark using the `parse` task and the `strings-list` target would be named
`parse-strings-list`. Oh and benchmarks based off micro targets are called also
microbenchmarks (since the goal of checking the performance of a specific area
transfers).

Below are details about the tasks and targets that ship with blackbench:

## Tasks

- `fmt`: standard Black formatting behaviour although safety checks will **always** be
  run
- `fmt-fast`: like `fmt` but using `--fast` so safety checks are disabled
- `parse`: only do blib2to3 parsing

(labels/format-task-danger)=

```{important}
The `fmt` task forces safety checks to run (by adding trailing newlines) or else it could
skew the data in a nasty way. Normally safety checks only run if changes are made so there's
a possibility one version of Black will have to do more work over the other one you're
comparing against, totally throwing off the results for any sort of comparisons.
```

## Targets

Targets are a bit more complex since there's two types: normal and micro. Normal targets
represent real-world code (and aim to do a decent job to representing real-world use
cases and performance). Micro targets are typically smaller and are focused on one area
of black formatting (and mostly exist to measure performance in a specific area, like
string processing).

**Normal targets:**

- `black/*`: source code files from {pypi}`Black` 21.6b0 (9 targets)
- `flit/*` & `filt_core/*`: source code files from {pypi}`Flit` 3.2.0 (3 targets)

**Micro targets:**

- `dict-literal`: a long dictionary literal
- `comments`: code that uses a lot of (maybe special) comments
- `list-literal`: a long list literal
- `nested`: nested functions, literals, if statements ... all the nested!
- `strings-list`: a list containing 100s of sometimes comma separated strings

(labels/task-compatibility)=

## Compatibility

While it would be great if blackbench could support all versions of Black, this is
difficult if not impossible since tasks use internal components of Black's
implementation. This provides a benchmarking speedup and is also unavoidable for lower
level tasks like `parse`. Due to this, each task imposes restrictions to what version of
Black their benchmarks can be run under:

- `fmt` and `fmt-fast`: >= 19.3b0
- `parse`: >= 21.5b1

## Useful commands

Blackbench does have a few commands that interact directly with tasks and targets:

`blackbench dump ${name}`

: Dumps the source code for a specific task or target.

  ```console
  dev@example:~$ blackbench dump fmt-fast
  from pathlib import Path

  import pyperf

  import black

  runner = pyperf.Runner()
  code = Path(r"{target}").read_text(encoding="utf8")


  def format_func(code):
      try:
          black.format_file_contents(code, fast=True, mode=black.FileMode({mode}))
      except black.NothingChanged:
          pass


  runner.bench_func("{name}", format_func, code)
  ```

`blackbench info`

: Lists all of the built-in tasks and targets.

  ```console
  dev@example:~$ blackbench info
  Tasks:
    1. fmt - Standard Black run although safety checks will *always* run
    2. fmt-fast - Standard Black run but safety checks are *disabled*
    3. parse - Only do blib2to3 parsing

  Normal targets:
    1. black/__init__ [1132 lines] - Black source code from 21.6b0
    2. black/brackets [334 lines] - Black source code from 21.6b0
    3. black/comments [272 lines] - Black source code from 21.6b0
    4. black/linegen [985 lines] - Black source code from 21.6b0
    5. black/lines [734 lines] - Black source code from 21.6b0
    6. black/mode [123 lines] - Black source code from 21.6b0
    7. black/nodes [843 lines] - Black source code from 21.6b0
    8. black/output [84 lines] - Black source code from 21.6b0
     9. black/strings [216 lines] - Black source code from 21.6b0
    10. flit/install [415 lines] - Flit source code from 3.2.0
    11. flit/sdist [216 lines] - Flit source code from 3.2.0
    12. flit_core/config [630 lines] - Flit source code from 3.2.0

  Micro targets:
    1. dict-literal [150 lines] - A long dictionary literal
    2. comments [97 lines] - Code that uses a lot of (maybe special) comments
    3. list-literal [150 lines] - A long list literal
    4. nested [41 lines] - Nested functions, literals, if statements ... all the nested!
    5. strings-list [52 lines] - A list containing 100s of sometimes comma separated strings
  ```
