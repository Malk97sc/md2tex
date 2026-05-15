"""Shared pytest fixtures for md2tex tests."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
MARKDOWN_DIR = FIXTURES_DIR / "markdown"
TEX_DIR = FIXTURES_DIR / "tex"


@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture()
def markdown_dir() -> Path:
    """Return the path to the Markdown fixtures directory."""
    return MARKDOWN_DIR


@pytest.fixture()
def tex_dir() -> Path:
    """Return the path to the TeX fixtures directory."""
    return TEX_DIR


def convert_markdown(md_content: str, french_quote: bool = False,
                     unnumbered: bool = False,
                     document_class: str = "article") -> str:
    """Run the md2tex conversion pipeline on a raw Markdown string.

    This replicates the conversion logic from ``md2tex.cli.md2tex``
    without file I/O, making it suitable for unit tests.
    """
    from md2tex.parser import parse
    from md2tex.renderer import RenderOptions, render_tex

    doc = parse(md_content)
    options = RenderOptions(
        document_class=document_class,
        unnumbered=unnumbered,
        french_quote=french_quote,
    )
    return render_tex(doc, options)
