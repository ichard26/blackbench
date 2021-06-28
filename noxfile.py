import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Union

import nox

THIS_DIR = Path(__file__).parent
REQ_DIR = THIS_DIR / "requirements"
WINDOWS = sys.platform.startswith("win")

SUPPORTED_PYTHONS = ["3.8", "3.9"]
_FLIT_EDITABLE_INSTALL = (
    "flit",
    "install",
    "--deps",
    "production",
    ("--pth" if WINDOWS else "--symlink"),
)

nox.needs_version = ">=2019.5.30"
nox.options.error_on_external_run = True

if sys.version_info < (3, 7, 0):
    print("ERROR: blackbench has no support for anything lower than Python 3.7.")
    sys.exit(2)

# --------- #
# UTILITIES #
# --------- #


_no_wipe: List[Path] = []


def wipe(session: nox.Session, path: Union[str, Path], once: bool = False) -> None:
    if "--install-only" in sys.argv:
        return

    if isinstance(path, str):
        path = Path.cwd() / path
    normalized = path.relative_to(THIS_DIR)

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
    if not ("-R" in sys.argv or "--reuse-existing-virtualenvs" in sys.argv):
        session.run(*_FLIT_EDITABLE_INSTALL, silent=True)
    session.install(black_req or "black")
    install_requirement(session, "tests-base")
    if coverage:
        install_requirement(session, "tests-cov")

    cmd = ["pytest"]
    if coverage:
        cmd.extend(["--cov", "--cov-branch", "--cov-context", "test", "--cov-append"])

    session.run(*cmd, *session.posargs)


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
    session.run(
        "pre-commit", "run", "--all-files", "--show-diff-on-failure", *session.posargs
    )


@nox.session()
def build(session: nox.Session) -> None:
    """Build distributions with flit."""
    session.install("flit")
    wipe(session, "dist")
    session.run("flit", "build", *session.posargs)


@nox.session(name="setup-env", venv_backend="none")
def setup_env(session: nox.Session) -> None:
    """Setup a basic (virtual) environment for manual testing."""
    env_dir = THIS_DIR / "venv"
    bin_dir = env_dir / ("Scripts" if WINDOWS else "bin")
    wipe(session, env_dir)
    session.run(sys.executable, "-m", "virtualenv", str(env_dir), silent=True)
    session.run(bin_dir / "python", "-m", "pip", "install", "flit", silent=True)
    session.run(bin_dir / "python", "-m", *_FLIT_EDITABLE_INSTALL, silent=True)
    activation_path = (bin_dir / "activate").relative_to(THIS_DIR)
    activation_str = (".\\" if WINDOWS else ". ") + str(activation_path)
    session.log(
        "Created environment named venv at project root,"
        f" you can activate it using `{activation_str}`."
    )
