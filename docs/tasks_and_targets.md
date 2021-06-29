# Tasks & targets

Blackbench comes with tasks and targets. Tasks represent a specific task Black has do
during formatting, and come with a specific template. Targets are the actual files Black
is run against to gauge performance. Together they create benchmarks that are ran using
[pyperf](https://pypi.org/project/pyperf).

Why not just ship ready-to-go benchmark scripts instead? Well, there's a few issues with
that: running static benchmarks limits the available configuration. Want to benchmark
Black with the magic trailing comma disabled? You'd have to edit each benchmark which is
annoying. And even if providing scripts for all of the different possible configurations
was possible, they would be annoying to maintain.

Benchmarks ran by blackbench are named using the task and target they are based off. For
example a benchmark using the `parse` task and the `strings-list.py` target would be
named `[parse]-[strings-list.py]`.

Below are details about the tasks and targets that ship with blackbench:

## Tasks

- `format`: standard Black formatting behaviour although safety checks will **always**
  be run
- `format-fast`: like `format` but using `--fast` so safety checks are disabled
- `parse`: only do blib2to3 parsing

(labels/format-task-danger)=

```{important}
The `format` task forces safety checks to run (by adding trailing newlines) or else it could
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

- `black/*`: a checkout of 21.6b0 of Black's source code (19 targets)

**Micro targets:**

- `strings-list.py`: a single list containing a few hundred of sometimes comma separated
  strings

(labels/task-compatibility)=

## Compatibility

While it would be great if blackbench could support all versions of Black, this is
difficult if not impossible since tasks use internal components of Black's
implementation. This provides a benchmarking speedup and is also unavoidable for lower
level tasks like `parse`. Due to this, each task imposes restrictions to what version of
Black their benchmarks can be run under:

- `format` and `format-fast`: >= 19.3b0
- `parse`: >= 21.5b1

## Useful commands

Blackbench does have a few commands that interact directly with tasks and targets:

`blackbench dump ${ID}`

: Dumps the source code for a specific task or target.

  ```console
  dev@example:~$ blackbench dump format-fast
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

: Lists all of the (IDs of the) built-in tasks and targets.

  ```console
  dev@example:~$ blackbench info
  Tasks:
    parse, format-fast, format

  Normal targets:
    1. black/__init__.py
    2. black/brackets.py
    3. black/cache.py
    4. black/comments.py
    5. black/concurrency.py
    6. black/const.py
    7. black/debug.py
    8. black/files.py
    9. black/linegen.py
    10. black/lines.py
    11. black/mode.py
    12. black/nodes.py
    13. black/numerics.py
    14. black/output.py
    15. black/parsing.py
    16. black/report.py
    17. black/rusty.py
    18. black/strings.py
    19. black/trans.py

  Micro targets:
    1. strings-list.py
  ```
