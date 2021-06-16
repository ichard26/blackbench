# mypy: disallow_untyped_defs=False

from click.testing import CliRunner

import blackbench

from .utils import DIR_SEP, replace_data_files


def test_info_cmd():
    with replace_data_files():
        results = CliRunner().invoke(blackbench.main, "info")
    # TODO: make orderness not an issue
    good = """\
Tasks:
  paint, format

Normal targets:
  1. goodbye-internet.pyi
  2. hello-world.py
  3. i{0}heard{0}you{0}like{0}nested.py

Micro targets:
  1. tiny.py
""".format(
        DIR_SEP
    )
    assert results.output == good
