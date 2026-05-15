import sys
import os
import click


class ParsingException(Exception):
    """Base class for all parsing exceptions."""


class IndentationException(ParsingException):
    """Error logs relative to list indentation."""

    logs = {
        "firstindent": (
            "ERROR. - inconsistant indentation in markdown list \n"
            "`@@TOKEN@@` \n"
            "all items must be as indented than the first list item or more."
        ),
        "multiplier": (
            "ERROR. inconsistant indentation level in list \n"
            "`@@TOKEN@@` \nall list items must share a common indentation multiplier.\n"
            "the first indented item defines the indentation multiplier."
        ),
    }

    def __init__(self, key: str, lstext: str) -> None:
        """Launch an IndentationException."""
        self.message = IndentationException.logs[key].replace("@@TOKEN@@", lstext)
        super().__init__(self.message)
        if not os.environ.get("MD2TEX_TUI"):
            click.echo(self.message)


class InputException(Exception):
    """Base class for all errors caused by user input: files not found, invalid files, etc."""

    logs = {
        "not_md": (
            "ERROR - filename `@@TOKEN@@` doesn't end with `.md` "
            "and doesn't seem to be a markdown file. exiting..."
        ),
        "not_inpath": "ERROR - input file `@@TOKEN@@` not found. exiting...",
        "not_template": "ERROR - custom tex template `@@TOKEN@@` not found. exiting...",
        "template_no_token": (
            "ERROR - custom tex template `@@TOKEN@@` does not contain a "
            "@@BODYTOKEN@@ key. cannot perform replacement."
        ),
        "not_outpath": (
            "ERROR - output directory or directories for path `@@TOKEN@@` don't "
            "seem to exist. create it and start again..."
        ),
        "outpath_slashes": (
            "ERROR - output file path `@@TOKEN@@` contains '/' and '\\'. "
            "please remove slashes or backslashes to continue."
            "exiting..."
        ),
        "document_class": (
            "ERROR - invalid value provided for argument `--document-class`: `@@TOKEN@@`. "
            "allowed values are `article` or `book`. exiting..."
        ),
    }

    def __init__(self, key: str, val: str | None = None) -> None:
        """Launch an InputException."""
        self.message = InputException.logs[key].replace("@@TOKEN@@", val or "")
        super().__init__(self.message)
        if not os.environ.get("MD2TEX_TUI"):
            click.echo(self.message)
            sys.exit(1)


class Warnings:
    """Display custom warning messages."""

    logs = {
        "outpath_extension": "WARNING - file extension of output file `@@TOKEN@@` changed to `.tex`",
        "list_deep_nesting": (
            "WARNING - deep list nesting. you may need to change base tex options in the header."
        ),
    }

    def __init__(self, key: str, val: str | None = None) -> None:
        """Display a warning message to the user."""
        self.message = Warnings.logs[key].replace("@@TOKEN@@", val or "")
        if not os.environ.get("MD2TEX_TUI"):
            click.echo(self.message)
