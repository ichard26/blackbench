import tempfile
from pathlib import Path

import pyperf

from blib2to3 import pygram

# First try the relevant function post-refactor in 21.5b1, and fallback
# to old function location.
try:
    from black.parsing import lib2to3_parse
except ImportError:
    from black import lib2to3_parse

runner = pyperf.Runner()
code =  Path(r"{target}").read_text(encoding="utf8")

with tempfile.TemporaryDirectory(prefix="blackbench-parsing-") as path:
    # Block the parser code from using any pre-existing cache.
    pygram.initialize(path)
    runner.bench_func("{name}", lib2to3_parse, code)
