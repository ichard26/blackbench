from pathlib import Path

import pyperf

runner = pyperf.Runner()
code = Path(r"{target}").read_text(encoding="utf8")


get_paint_brush = lambda: "paintsy-brush"
get_black_paint = lambda: "■"
artsy = lambda **kwargs: "■■■■■■■■■■■■■"


def paint_func(code):
    try:
        brush = get_paint_brush()
        paint = get_black_paint()
        artsy(tool=brush, using=paint, target=code)
    except RuntimeError:
        pass


runner.bench_func("{name}", format_func, code)
