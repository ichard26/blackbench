# Quickstart

## Installation

```{note}
Currently blackbench isn't available on PyPI. Although publishing to PyPI is planned
once blackbench reaches a state where it's generally usable. For now, you have two
main choices for installing blackbench.
```

```{important}
Blackbench requires Python 3.8 or higher to run. Note that this is sigificantly higher than
Black's runtime requirement of 3.6.2+.
```

The first one is going to the releases page from this project's GitHub homepage and
downloading the wheel for the version you'd like. Then once available locally, you can
pass that file to pip:

```bash
pip install path/to/the/downloaded/wheel.whl
```

The other one is installing via a VSC URL with pip. This will pull down the newest
revision of blackbench (in other words, whatever is in `main`). Unreleased versions of
blackbench should work just fine, but may have bugs and other half-implemented features.

```bash
pip install git+git://github.com/ichard26/blackbench
```

`````{tip}

You can enable tab completion following these instructions:

  ````{tab} Bash
  Add this to ``~/.bashrc``:

  ```bash
  eval "$(_BLACKBENCH_COMPLETE=bash_source blackbench)"
  ```
  ````

  ````{tab} Zsh
  Add this to ``~/.zshrc``:

  ```zsh
  eval "$(_BLACKBENCH_COMPLETE=zsh_source blackbench)"
  ```
  ````

  ````{tab} Fish
  Add this to ``~/.config/fish/completions/blackbench.fish``:

  ```fish
  eval (env _BLACKBENCH_COMPLETE=fish_source blackbench)
  ```

  ````

Oh and my apologies if your shell isn't supported, I'm just using Click's built-in framework so
it's out of my control.
`````

## Tuning your system

To get reliable results, the system should be tuned to avoid system jitter.

```{warning}
Note the suggested modifications may not be supported for your specific environment and
also can be annoying to undo (a simple reboot should clear them though).
```

1. `pyperf system tune`.

1. \[optional\] Isolate CPUs + other low level tweaks. See Victor Stinner's excellent
   article ["My journey to stable benchmark, part 1 (system)"][isolating-cpus]. (Linux
   only)

```{seealso}
[Running benchmarks: Benchmark stability](labels/benchmark-stability).
```

## Running benchmarks

1. Install one of the revisions of Black you'd like to compare.
1. Call the `run` command with a filepath to dump results as the argument.
1. Repeat steps 1-2 until you have tested all of the revisions.

## Comparing runs

1. Run `pyperf compare_to` passing in the result files from the previous step.
1. Celebrate because you've successfully used blackbench to benchmark and compare
   different revisions of Black!

## What's next?

See the rest of the User Guide for an indepth explanation and guide to using blackbench
effectively, to learn blackbench's more advanced features, and overall just improve your
benchmarking game.

Thank you for using blackbench!

```{todo}
Overhaul the quickstart document to include examples and to be more detailed. In other
words, make it much easier to follow.
```

[isolating-cpus]: https://vstinner.github.io/journey-to-stable-benchmark-system.html
