import tempfile
from pathlib import Path

import pyperf

from blib2to3.pytree import Node, Leaf
from blib2to3 import pygram, pytree
from blib2to3.pgen2 import driver
from blib2to3.pgen2.parse import ParseError
from black.nodes import syms


class InvalidInput(ValueError):
    """Raised when input source code fails all parse attempts."""


runner = pyperf.Runner()
code = Path(r"{target}").read_text(encoding="utf8")
pygram.initialize(tempfile.gettempdir())

grammars = [
    # Python 3.7+
    pygram.python_grammar_no_print_statement_no_exec_statement_async_keywords,
    # Python 3.0-3.6
    pygram.python_grammar_no_print_statement_no_exec_statement,
    # Python 2.7 with future print_function import
    pygram.python_grammar_no_print_statement,
    # Python 2.7
    pygram.python_grammar,
]


def blib2to3_parse(src_txt: str) -> Node:
    if not src_txt.endswith("\n"):
        src_txt += "\n"

    for grammar in grammars:
        drv = driver.Driver(grammar, pytree.convert)
        try:
            result = drv.parse_string(src_txt, True)
            break

        except ParseError as pe:
            lineno, column = pe.context[1]
            lines = src_txt.splitlines()
            try:
                faulty_line = lines[lineno - 1]
            except IndexError:
                faulty_line = "<line number missing in source>"
            exc = InvalidInput("Cannot parse: " + str(lineno) + ":" + str(column) + ":" + str(faulty_line))
    else:
        raise exc from None

    if isinstance(result, Leaf):
        result = Node(syms.file_input, [result])
    return result


runner.bench_func("{name}", blib2to3_parse, code)
