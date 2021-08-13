import pyperf


def do() -> None:
    assert 1 + 2 == 3


runner = pyperf.Runner()
runner.bench_func("dummy", do)
