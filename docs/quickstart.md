# Quickstart

## Installation

**Prerequisite:** Python 3.8 or higher[^1]

Blackbench is available through PyPI so it's pretty easy to install.

```bash
python -m pip install blackbench
```

Your other option is installing via a VSC URL with pip. This will pull down the newest
revision of blackbench (in other words, whatever is in `main`). Unreleased versions of
blackbench should work just fine, but may have bugs and other half-implemented features.

```bash
python -m pip install git+git://github.com/ichard26/blackbench
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

To get reliable results - which is needed so comparisons still make sense - the system
should be tuned to avoid system jitter. While there's a lot of OS-specific / low-level
tuning (eg. `isolcpu=1` on Linux) you can do to cut down on the benchmark noise, they
can take a fair bit of effort to setup correctly (not to mention if they're even
compatible with your system). So to avoid making this quick start more like a "long
guide" here's some quick and easy things you can do to increase benchmark stability:

```{warning}
Note the suggested modifications may not be supported for your specific environment and
also can be annoying to undo (a simple reboot should clear them though).
```

- Run `pyperf system tune`[^2] - personally this command feels like magic, but in
  essence it tries to configure your system automatically according to this
  [list of operations][pyperf-system-ops]
- Use the pyperf `--affinity` option to pin worker processes to a specific CPU core
  (since it's a pyperf option, you'll need to precede it with `--` after your blackbench
  arguments)
- Try to leave your system alone while it's benchmarking as much as reasonably possible
- Oh and the classic advice of closing down unnecessary background processes still
  applies :)

If you're curious for more, don't worry! Further in the User Guide will be more detailed
information on this topic.

## Running benchmarks

1. Install one of the revisions of Black you'd like to compare.

1. Call the `run` command with a filepath to dump results as the argument.

   ```console
   dev@example:~/blackbench$ blackbench run normal.json -- --affinity 1
   [*] Versions: blackbench: 21.7.dev2, pyperf: 2.2.0, black: 21.6b0
   [*] Created temporary workdir at `/tmp/blackbench-workdir-ly0edox8`.
   [*] Alright, let's start!
   [*] Running `fmt-black/__init__` benchmark (1/17)
   .....................
   fmt-black/__init__: Mean +- std dev: 1.50 sec +- 0.05 sec
   [*] Took 41.291 seconds.
   [*] Running `fmt-black/brackets` benchmark (2/17)

   [snipped ...]

   [*] Cleaning up.
   [*] Results dumped.
   [*] Blackbench run finished in 373.794 seconds.
   ```

1. Repeat steps 1-2 until you have tested all of the revisions.

```{note}
The default configuration uses the `fmt` task and all targets (ie. tests standard Black
behaviour with safety checks against all available code files). This can be pretty slow
depending on how fast your machine is. A quick fix would be to use `--fast` to collect
less values.
```

## Comparing runs

1. Run `pyperf compare_to` passing in the result files from the previous step.[^3]

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

1. Celebrate because you've successfully used blackbench to benchmark and compare
   different revisions of Black! 🎉

## What's next?

See the rest of the User Guide for an indepth explanation and guide to using blackbench
effectively, to learn blackbench's more advanced features, and overall get better at
benchmarking. You can also take a look at the [pyperf documentation][pyperf-docs] since
blackbench heavily depends on it for many parts of its functionality.

Thank you for using blackbench and I hope you make good use out of it!

[^1]: I know Black's Python runtime requirement is probably lower (it's 3.6.2+ as of writing)
    but given this is a developer-focused tool, I consider it fine (especially since I don't
    see blackbench's requirement being bumped anytime soon).

[^2]: Don't worry, pyperf should've been installed alongside blackbench since the latter
    depends on it.

[^3]: These numbers aren't actually representative of the slowdown experimental string
    processing causes, I got these numbers without taking any care to get stable results (so
    I could write these docs quickly).

[pyperf-docs]: https://pyperf.readthedocs.io/en/stable/
[pyperf-system-ops]: https://pyperf.readthedocs.io/en/stable/system.html#system-cmd-ops
