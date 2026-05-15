"""Intermediate representation nodes for the md2tex pipeline.

These dataclasses represent the block-level structure of a Markdown
document. Inline formatting (bold, italic, links, etc.) is handled
as regex transforms on the text content during rendering, not as
separate IR nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# -- Block-level nodes -------------------------------------------------------


@dataclass
class Heading:
    """A Markdown heading (``# ...`` through ``###### ...``)."""

    level: int
    text: str


@dataclass
class Paragraph:
    """A block of plain text (one or more non-blank lines)."""

    text: str


@dataclass
class CodeBlock:
    """A fenced code block (`` ``` ``).

    If *language* is ``None``, no syntax highlighting is applied.
    """

    code: str
    language: str | None = None


@dataclass
class BlockQuote:
    """A block quotation (lines starting with ``>``)."""

    text: str


@dataclass
class ListItem:
    """A single item inside a list, potentially with nested children."""

    text: str
    children: ListBlock | None = None


@dataclass
class ListBlock:
    """An ordered or unordered list."""

    ordered: bool
    items: list[ListItem] = field(default_factory=list)


@dataclass
class HorizontalRule:
    """A horizontal rule (``---``, ``***``, or ``___``)."""


@dataclass
class FootnoteDef:
    """A footnote definition (``[^N]: ...``)."""

    key: str
    text: str


@dataclass
class FootnoteRef:
    """A footnote reference marker in body text (``[^N]``)."""

    key: str


@dataclass
class TableRow:
    cells: list[str]


@dataclass
class Table:
    alignments: list[str]
    headers: TableRow
    rows: list[TableRow]


# -- Type alias for a parsed document ----------------------------------------

Block = Heading | Paragraph | CodeBlock | BlockQuote | ListBlock | HorizontalRule | FootnoteDef | Table

Document = list[Block]
