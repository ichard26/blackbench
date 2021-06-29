# Contributing

Hey thanks for considering contributing to blackbench! It's awesome to see you here.
Anyway, there's a lot of ways you can contribute to blackbench, whether that's opening a
constructive bug report or feature request, writing docs, to actually writing some code.

## Setting up development environment

### Requirements

- **CPython 3.8 or higher**

- [**Nox**][nox]

  All development commands are managed by Nox which provides automated environment
  provisioning. For us, it's basically a task runner. I strongly recommend
  [using pipx][pipx].

- [**pre-commit**][pre-commit] *\[optional\]*

  pre-commit runs Git commit hooks that assert a baseline of quality. Once again, [pipx]
  is encouraged.

### Steps

1. Fork the blackbench project on GitHub if you haven't already done so.

1. Clone your fork and `cd` into the resulting directory.

   ```console
   dev@example:~$ git clone https://github.com/${USERNAME}/blackbench.git
   Cloning into 'blackbench'...
   remote: Enumerating objects: 244, done.
   remote: Counting objects: 100% (244/244), done.
   remote: Compressing objects: 100% (141/141), done.
   remote: Total 244 (delta 85), reused 212 (delta 58), pack-reused 0
   Receiving objects: 100% (244/244), 154.29 KiB | 360.00 KiB/s, done.
   Resolving deltas: 100% (85/85), done.
   dev@example:~$ cd blackbench
   dev@example:~/blackbench$
   ```

1. Add the fork's parent (ie. upstream) as an additional remote.

   ```console
   dev@example~/blackbench$ git remote add upstream https://github.com/ichard26/blackbench.git
   ```

1. If pre-commit is available, install the Git pre commit hooks.

   ```console
   dev@example:~/blackbench$ pre-commit install
   pre-commit installed at .git/hooks/pre-commit
   ```

1. Run the `setup-env` session with Nox.

   You'll use this virtual environment to run blackbench from source (ie, during manual
   testing). Flit's editable install feature will be used so don't worry about
   recreating the environment after changing something, they should be instantly
   reflected!

   ```console
   dev@example:~/blackbench$ nox -s setup-env
   nox > Running session setup-env
   nox > /home/dev/.local/pipx/venvs/nox/bin/python -m virtualenv /home/dev/blackbench/venv
   nox > /home/dev/blackbench/venv/bin/python -m pip install flit
   nox > /home/dev/blackbench/venv/bin/python -m flit install --deps production --symlink
   nox > Virtual environment at project root named `venv` ready to go!
   nox > Session setup-env was successful.
   ```

   ```{important}
   The environment created by `setup-env` is **only** for manual testing. Automated testing
   or other development commands should be done via the sessions configured in `noxfile.py`.
   This is why the created virtual environment only has the dependencies needed to
   run blackbench.
   ```

1. Activate the created virtual environment.

   `````{tab} Unix/macOS

      ````{tab} Bash

         ```console
         dev@example:~/blackbench$ . venv/bin/activate
         (venv) dev@example:~/blackbench$
         ```

      ````

      ````{tab} Zsh

         ```console
         dev@example:~/blackbench$ . venv/bin/activate.zsh
         (venv) dev@example:~/blackbench$
         ```

      ````

      ````{tab} Fish

         ```console
         dev@example:~/blackbench$ source venv/bin/activate.fish
         (venv) dev@example:~/blackbench$
         ```

      ````

   `````

   ````{tab} Windows

   ```doscon
   C:\Users\dev\blackbench> venv\Scripts\activate
   (venv) C:\Users\dev\blackbench>
   ```

   ````

1. Celebrate! ... and then get to work on that change you've been thinking about :)

## Development commands

As already mentioned, [Nox] is basically a task runner here. Most development commands
are already configured in `noxfile.py` so running them correctly is easy as can be.

All the Nox sessions should support both `-r` and `-R`, so if the sessions are too slow
(especially for rapid iteration during development), try of them. The only major
exception is `setup-env` but that one doesn't use a Nox-provisioned environment anyway.

Also, it's possible to pass extra arguments to any the sessions' main command. Want to
add `-k "not provided"` to the pytest run in `tests`? That's possible via
`nox -s tests -- -k "not provided"`.

```{seealso}
[Nox: Command-line usage][nox-usage].
```

### Testing

To run the test suite, just run the `tests` session:

```bash
$ nox -s tests
```

If you want to collect coverage too, there's the `tests-cov` sessions for that:

```bash
$ nox -s tests-cov
```

Nox has one more awesome feature and that's making it really easy to run the test suite
against multiple versions of Python at once. Matter of fact, the commands above will
make Nox run the test session for every supported Python version it can find. You can
select a single version by prepending the version (eg. `nox -s tests-3.9`).

```{tip}
If you need to run the test suite with a specific version of Black you can use
the `--black-req` option. Eg. `nox -s tests-3.8 -- --black-req "black==21.5b2"`.
Note that the `--` is important since the option was implemented at the session
level and is 100% custom.
```

### Linting

Calling pre-commit to run linters is as simple as:

```bash
$ nox -s lint
```

### Docs

There's two sessions for documentation, which one you choose depends on what your goal
is. If you're looking to do a complete and clean (re)build of the documentation, just
run the aptly named `docs` session:

```bash
$ nox -s docs
```

BUT, if you're actively making changes to the documentation, having it automatically
rebuild and refresh on changes will make your life easier. That's available using:

```bash
$ nox -s docs-live
```

Once the first build has been completed, there should be a link that serves the built
documentation. As mentioned, the page will automagically refresh on changes!

## Area-specific notes

### Adding a new target

At the moment of writing blackbench doesn't come with much benchmark data to run Black
against. So I'd appreciate more code files to throw to Black.

I'm looking for two kinds of targets: "normal" and "micro" . Normal targets should
represent real-world code (so the benchmarking data actually represents real-world
performance). Micro targets should be small and are focused on one area of Black
formatting (and mostly exist to measure performance in a specific area, like string
processing).

In terms of guidelines: normal targets shouldn't be bigger than ~2000 lines (this is to
keep time requirements to run the benchmark based off the target manageable), and micro
targets shouldn't be bigger than ~400 lines. Oh and for micro targets, make sure their
focus hasn't been already covered by another target.

### Release process

```{todo}
Need to actually write up a release process, but that will wait until blackbench hits
beta or alpha.

note-to-self: don't forget about the `build` session
```

## PR guidelines

To make it easier for all of us to collaborate and get your PR merged, there's a few
guidelines to be noted:

- If your PR has user-facing changes (eg. new target, bugfix), please add a changelog
  entry.
- Your PR should try to maintain excellent project coverage, although this isn't a
  blocker.
- Please include an explanation for the changes (and maybe a summary too if complicated
  enough) in the commit message.
- If CI fails, please address it, especially if the test suite failed since
  compatibility with muliple systems and environments must be maintained.
- You should expect somesort of response within three days. If not, feel free to ping
  @ichard26.

## Getting help

If you get stuck, don't hesistate to ask for help on the relevant issue or PR.
Alternatively, we can talk in the #black-formatter[^1] text channel on Python Discord.
Here's an [invite link][discord]!

[^1]: I know it's specifically for Black, but blackbench is a development tool for Black so I
    consider it acceptable - although I never asked ... but then again, I am a maintainer of
    Black so yeah :p

[discord]: https://discord.gg/RtVdv86PrH
[nox]: https://nox.thea.codes/en/stable/
[pipx]: https://packaging.python.org/guides/installing-stand-alone-command-line-tools/
[pre-commit]: https://pre-commit.com/
