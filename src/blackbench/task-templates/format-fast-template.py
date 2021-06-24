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
