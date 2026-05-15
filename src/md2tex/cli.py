"""md2tex CLI -- convert a Markdown file to a LaTeX file."""

from __future__ import annotations

import importlib.resources
import os
import re
from pathlib import Path

import click

from md2tex.errors_warnings import InputException, Warnings
from md2tex.parser import parse
from md2tex.renderer import RenderOptions, render_tex


def _default_template_path() -> str:
    """Resolve the path to the bundled default TeX template.

    Uses ``importlib.resources`` so that it works correctly when the
    package is installed as a wheel or in editable mode.
    """
    return str(importlib.resources.files("md2tex").joinpath("data/template.tex"))


@click.command("md2tex")
@click.argument("inpath")
@click.option(
    "-o", "--output-path", "outpath", default=None,
    help="Optional. A custom output path. Defaults to `output/{input_file_name}.tex`.",
)
@click.option(
    "-c", "--complete-tex-file", "tex", is_flag=True, default=False,
    help=(
        "Optional. If provided, a complete TeX file will be created from a template "
        "(with preamble and tables of content). If not provided, only the contents of "
        "the Markdown file are translated. Can be used with `-t` to use a custom, "
        "user-provided TeX template. Defaults to False."
    ),
)
@click.option(
    "-t", "--custom-tex-template", "template", default=None,
    help=(
        "Optional. If provided, a custom TeX template will be used to create a complete "
        "TeX file. This argument must be used with `-c` and the TeX template must contain "
        "a `@@BODYTOKEN@@` between its `\\begin{document}` and `\\end{document}` to perform "
        "the replacement. Defaults to the bundled template."
    ),
)
@click.option(
    "-f", "--french-quote", "french_quote", is_flag=True, default=False,
    help=(
        "Optional. If provided, Markdown inline quotes will be converted as french "
        "quotes `\\enquote{}` instead of anglo-saxon quotes. Defaults to False."
    ),
)
@click.option(
    "-u", "--unumbered-headers", "unnumbered", is_flag=True, default=False,
    help=(
        "Optional. If provided, Markdown headers will be translated as TeX unnumbered "
        "headers/sections. Defaults to False: the headers are numbered by default."
    ),
)
@click.option(
    "-d", "--document-class", "document_class", default="article",
    help=(
        "Optional. Sets the class of the TeX document. Possible values are: "
        "`book`|`article`. Defaults to `article`."
    ),
)
@click.option(
    "--code-backend",
    type=click.Choice(["auto", "minted", "listings"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Code block backend strategy for complete TeX generation.",
)
@click.option(
    "--shell-escape",
    "shell_escape",
    is_flag=True,
    default=False,
    help="Enable shell-escape assumptions for minted when using code backend auto/minted.",
)
def md2tex(
    inpath: str,
    outpath: str | None = None,
    tex: bool = False,
    template: str | None = None,
    french_quote: bool = False,
    unnumbered: bool = False,
    document_class: str = "article",
    code_backend: str = "auto",
    shell_escape: bool = False,
) -> str:
    """Convert a Markdown file to a TeX file.

    INPATH is the path to the *.md file to convert to TeX.
    """
    # Resolve default template
    if template is None:
        template = _default_template_path()

    if inpath.lower() in ("tui", "interactive"):
        try:
            from md2tex.tui.app import Md2TexApp
        except ImportError:
            click.echo("ERROR - The TUI feature requires 'textual'. Please install it using `pip install .[tui]` or `uv sync --extra tui`.")
            import sys
            sys.exit(1)
        Md2TexApp().run()
        return ""

    from md2tex.services import convert_markdown_to_tex

    data, final_outpath = convert_markdown_to_tex(
        inpath=inpath,
        outpath=outpath,
        tex=tex,
        template=template,
        french_quote=french_quote,
        unnumbered=unnumbered,
        document_class=document_class,
        code_backend=code_backend.lower(),
        shell_escape=shell_escape,
    )

    click.echo(f"FINISHED - file conversion completed and saved to `{final_outpath}`")
    return data
