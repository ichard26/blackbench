from pathlib import Path

import pyperf

import black

runner = pyperf.Runner()
code = Path(r"{target}").read_text(encoding="utf8")


def format_func(code):
    try:
        black.format_file_contents(code, fast=False, mode=black.FileMode({mode}))
    except black.NothingChanged:
        pass


# Add newlines that Black will strip out to force safety checks to run.
# Without it safety checks only run if changes are made. There’s a possibility
# one version of Black will have to do more work over another one. This
# would totally throw off the results for any sort of comparisons.
code = code + "\n\n\n"
runner.bench_func("{name}", format_func, code)
