import contextlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Tuple, Union

import nox

THIS_DIR = Path(__file__).parent
MAIN_MODULE = THIS_DIR / "src" / "blackbench" / "__init__.py"
CHANGELOG = THIS_DIR / "docs" / "changelog.md"
REQ_DIR = THIS_DIR / "requirements"
WINDOWS = sys.platform.startswith("win")
_FLIT_EDITABLE = "--pth" if WINDOWS else "--symlink"

SUPPORTED_PYTHONS = ["3.8", "3.9"]

nox.needs_version = ">=2019.5.30"
nox.options.error_on_external_run = True

if sys.version_info < (3, 8, 0):
    print("ERROR: blackbench has no support for anything lower than Python 3.8.")
    sys.exit(2)

# --------- #
# UTILITIES #
# --------- #


def get_today_date() -> str:
    """Return a string representing today's date suitable in documentation."""
    # fmt: off
    month_mapping = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December",
    }
    # fmt: on
    today = datetime.now()
    day_str = str(today.day)
    month = month_mapping[today.month]
    if today.day in (11, 12, 13):
        day_suffix = "th"
    elif day_str.endswith("1"):
        day_suffix = "st"
    elif day_str.endswith("2"):
        day_suffix = "nd"
    elif day_str.endswith("3"):
        day_suffix = "rd"
    else:
        day_suffix = "th"

    return f"{month} {today.day}{day_suffix}, {today.year}"


_no_wipe: List[Path] = []


def wipe(session: nox.Session, path: Union[str, Path], once: bool = False) -> None:
    if "--install-only" in sys.argv:
        return

    if isinstance(path, str):
        path = Path.cwd() / path
    normalized = path.relative_to(Path.cwd())

    if not path.exists():
        return

    if once:
        if not any(path == entry for entry in _no_wipe):
            _no_wipe.append(path)
        else:
            return

    if path.is_file():
        session.log(f"Deleting `{normalized}` file.")
        path.unlink()
    elif path.is_dir():
        session.log(f"Deleting `{normalized}` directory.")
        shutil.rmtree(path)


def install_requirement(session: nox.Session, name: str) -> None:
    path = (REQ_DIR / f"{name}.txt").relative_to(THIS_DIR)
    session.install("-r", str(path))


def do_docs(session: nox.Session, *, live: bool) -> None:
    session.install(".")
    install_requirement(session, "docs-base")
    if live:
        install_requirement(session, "docs-live")

    session.cd("docs")
    wipe(session, "_build")

    cmd: Tuple[str, ...]
    if not live:
        cmd = ("sphinx-build", ".", "_build", "-W", "--keep-going", "-n")
    else:
        cmd = ("sphinx-autobuild", ".", "_build", "-a", "-n")
    session.run(*cmd, *session.posargs)
    if not live:
        uri = (THIS_DIR / "docs" / "_build" / "index.html").as_uri()
        session.log(f"Built docs: {uri}")


def do_tests(session: nox.Session, *, coverage: bool) -> None:
    # Allow running test suite with a specific version of Black installed.
    # TODO: maybe consider dropping this and expect it to be done manually
    # using the environment created by setup-env. Although that would require
    # installing the test suite dependencies in that environment too, which
    # I am not too keen on :/
    black_req = ""
    if "--black-req" in session.posargs:
        index = session.posargs.index("--black-req")
        black_req = session.posargs[index + 1]
        del session.posargs[index]
        del session.posargs[index]

    session.install("flit")
    # Use editable installs even without coverage because it's faster.
    session.run("flit", "install", _FLIT_EDITABLE, silent=True)
    session.install(black_req or "black")
    install_requirement(session, "tests-base")
    if coverage:
        install_requirement(session, "tests-cov")

    cmd = ["pytest"]
    if coverage:
        cmd.extend(["--cov", "--cov-branch", "--cov-context", "test", "--cov-append"])
    session.run(*cmd, *session.posargs)


def modified_files_in_git(*args: str) -> int:
    return subprocess.run(
        ["git", "diff", "--no-patch", "--exit-code", *args],
        capture_output=True,
    ).returncode


def create_git_tag(session: nox.Session, tag_name: str, *, message: str) -> None:
    session.run(
        # fmt: off
        "git", "tag", "-m", message, tag_name,
        # fmt: on
        external=True,
        silent=True,
    )


def commit_files(session: nox.Session, filepaths: List[Path], *, message: str) -> None:
    session.run("git", "add", *map(str, filepaths), external=True, silent=True)
    session.run("git", "commit", "-m", message, external=True, silent=True)


def next_development_version(version: str) -> str:
    """
    Bump the minor* version AND replace any pre-release stuff with +dev1.

    *unless the minor version is 12, then time for next year!
    """
    year_str, other = version.split(".", maxsplit=1)
    year = int(year_str)
    # Basically this regex matches everything after the minor number, hopefully.
    minor = int(re.sub(r"[^\d]+\d+", "", other))
    if minor != 12:
        minor += 1
    else:
        year += 1
        minor = 0
    return f"{year}.{minor}+dev1"


def update_version(session: nox.Session, version: str, filepath: Path) -> None:
    with open(filepath, encoding="utf-8") as f:
        lines = f.read().splitlines()

    for index, line in enumerate(lines):
        if line.startswith("__version__"):
            lines[index] = f'__version__ = "{version}"'
            break
    else:
        session.error("Couldn't find __version__ in {filepath}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


def update_changelog(session: nox.Session, version: str, filepath: Path) -> None:
    """Update the changelog for both a new release and development."""
    with open(filepath, encoding="utf-8") as f:
        lines = f.read().splitlines()

    if version != "<unreleased>":
        for index, line in enumerate(lines):
            if line == "## Unreleased":
                # Let's replace that unreleased text with the actual version
                # and fix up that date of release.
                lines[index] = f"## {version}"
                lines[index + 2] = f"Date of release: {get_today_date()}"
                break
        else:
            session.error("Couldn't find changelog section for next release")
    else:
        # Grab the title and newline right after it
        updated_lines = [*lines[0:2]]
        # ... then add some boilerplace
        updated_lines.append("## Unreleased\n")
        updated_lines.append("Date of release: *n/a*\n")
        updated_lines.append("**Bugfixes & enhancements**:\n")
        updated_lines.append("- *so far it's looking like a desert*\n")
        # and finally add back the rest of the changelog.
        updated_lines.extend(lines[2:])
        lines = updated_lines

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")


@contextlib.contextmanager
def isolated_temporary_checkout(session: nox.Session) -> Iterator[Path]:
    """Make a clean checkout of a given version in a temporary dir."""
    with tempfile.TemporaryDirectory(prefix="blackbench-release-") as _workdir:
        workdir = Path(_workdir)
        session.run(
            # fmt: off
            "git", "clone",
            "--depth", "1",
            "--config", "core.autocrlf=false",
            "--",
            ".", str(workdir),
            # fmt: on
            external=True,
            silent=True,
        )
        yield workdir


# -------------------- #
# DEVELOPMENT COMMANDS #
# -------------------- #


@nox.session()
def docs(session: nox.Session) -> None:
    """Build a clean copy of the Sphinx documentation."""
    do_docs(session, live=False)


@nox.session(name="docs-live")
def live_docs(session: nox.Session) -> None:
    """Like docs, but with auto building and refreshing."""
    do_docs(session, live=True)


@nox.session(python=SUPPORTED_PYTHONS)
def tests(session: nox.Session) -> None:
    """Run test suite."""
    do_tests(session, coverage=False)


@nox.session(name="tests-cov", python=SUPPORTED_PYTHONS)
def tests_cov(session: nox.Session) -> None:
    """Like tests, but with coverage."""
    ci = False
    if "--ci" in session.posargs:
        ci = True
        session.posargs.remove("--ci")

    wipe(session, THIS_DIR / ".coverage", once=True)
    wipe(session, THIS_DIR / "htmlcov")
    wipe(session, THIS_DIR / "coverage.xml")

    do_tests(session, coverage=True)
    if not ci:
        session.run("coverage", "html")
    else:
        session.run("coverage", "xml")


@nox.session()
def lint(session: nox.Session) -> None:
    """Run linters and formatters."""
    install_requirement(session, "lint-base")
    session.run("pre-commit", "run", "--all-files", "--show-diff-on-failure", *session.posargs)


@nox.session(name="do-release")
def do_release(session: nox.Session) -> None:
    """Do a release to PyPI."""
    # TODO: maybe add version validation
    if modified_files_in_git() or modified_files_in_git("--staged"):
        session.error("Repository not clean, please remove, unstage, or commit your changes")

    if not len(session.posargs):
        session.error("Usage: nox -s publish -- <version> [publish-args]")
    else:
        version = session.posargs[0]

    update_version(session, version, MAIN_MODULE)
    update_changelog(session, version, CHANGELOG)
    commit_files(session, [MAIN_MODULE, CHANGELOG], message=f"Prepare for release {version}")
    create_git_tag(session, version, message=f"Release {version}")

    with isolated_temporary_checkout(session) as workdir:
        session.chdir(workdir)
        session.install("flit")
        session.run("flit", "publish", *session.posargs[1:])

    session.chdir(THIS_DIR)
    update_version(session, next_development_version(version), MAIN_MODULE)
    update_changelog(session, "<unreleased>", CHANGELOG)
    commit_files(session, [MAIN_MODULE, CHANGELOG], message="Let's get back to development")
    session.log("Alright, just do a push to GitHub and everything should be done")
    session.log("If you're paranoid, go ahead, verify that things are fine")
    session.log("If not, sit back and relax, you just did a release 🎉")


@nox.session(name="setup-env", venv_backend="none")
def setup_env(session: nox.Session) -> None:
    """Setup a basic (virtual) environment for manual testing."""
    env_dir = THIS_DIR / "venv"
    bin_dir = env_dir / ("Scripts" if WINDOWS else "bin")
    wipe(session, env_dir)
    session.run(sys.executable, "-m", "virtualenv", str(env_dir), silent=True)
    session.run(bin_dir / "python", "-m", "pip", "install", "flit", silent=True)
    session.run(bin_dir / "python", "-m", "flit", "install", _FLIT_EDITABLE, silent=True)
    session.run(bin_dir / "python", "-m", "pip", "install", "black", silent=True)
    session.log("Virtual environment at project root named `venv` ready to go!")
