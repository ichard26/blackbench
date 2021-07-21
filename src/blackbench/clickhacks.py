"""
Code to change Click's behaviour in a (maybe unsupported) way.

- Custom Command class that enforces a blank line around options in help output. I
  hated the change in Click 8.x that removed the blank lines and caused the help output
  to look like one giant wall of text.

P.S. I'm sorry to whoever has to touch (or maintain!) this code.
"""


from typing import Sequence, Tuple

import click
import click.core
from click._compat import term_len
from click.formatting import iter_rows, measure_table, wrap_text


class _SpacedHelpFormatter(click.formatting.HelpFormatter):
    def write_dl(
        self, rows: Sequence[Tuple[str, str]], col_max: int = 30, col_spacing: int = 2
    ) -> None:
        """Writes a definition list into the buffer.  This is how options
        and commands are usually formatted.
        :param rows: a list of two item tuples for the terms and values.
        :param col_max: the maximum width of the first column.
        :param col_spacing: the number of spaces between the first and
                            second column.
        """
        rows = list(rows)
        widths = measure_table(rows)
        if len(widths) != 2:  # pragma: no cover
            raise TypeError("Expected two columns for definition list")

        first_col = min(widths[0], col_max) + col_spacing

        for first, second in iter_rows(rows, len(widths)):
            self.write(f"{'':>{self.current_indent}}{first}")
            if not second:  # pragma: no cover
                self.write("\n")
                continue
            if term_len(first) <= first_col - col_spacing:
                self.write(" " * (first_col - term_len(first)))
            else:
                self.write("\n")
                self.write(" " * (first_col + self.current_indent))

            text_width = max(self.width - first_col - 2, 10)
            wrapped_text = wrap_text(second, text_width, preserve_paragraphs=True)
            lines = wrapped_text.splitlines()

            if lines:
                self.write(f"{lines[0]}\n")

                for line in lines[1:]:
                    self.write(f"{'':>{first_col + self.current_indent}}{line}\n")

            self.write("\n")  # pragma: no cover


class _CustomHelpContext(click.Context):
    formatter_class = _SpacedHelpFormatter


class CustomHelpCommand(click.core.Command):
    context_class = _CustomHelpContext
