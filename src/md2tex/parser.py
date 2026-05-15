"""Block-level Markdown parser.

Reads raw Markdown text and produces a list of IR nodes (see
:mod:`md2tex.nodes`).  Block extraction happens on the *raw* text
before any TeX escaping, which fixes the old pipeline bug where ``>``
was escaped before block-quote matching.

Inline formatting is **not** parsed here -- it is applied as regex
transforms during rendering.
"""

from __future__ import annotations

import re

from .helpers import process_list_indentation
from .minted import languages
from .nodes import (
    BlockQuote,
    CodeBlock,
    Document,
    FootnoteDef,
    Heading,
    HorizontalRule,
    ListBlock,
    ListItem,
    Paragraph,
    Table,
    TableRow,
)


def parse(text: str) -> Document:
    """Parse raw Markdown into a list of block-level IR nodes.

    Parameters
    ----------
    text:
        The raw Markdown source.

    Returns
    -------
    Document:
        Ordered list of block-level nodes.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    blocks: Document = []

    # Phase 1: extract fenced code blocks (verbatim, before anything else)
    text, code_blocks = _extract_code_blocks(text)

    # Phase 2: extract footnote definitions
    text, footnote_defs = _extract_footnote_defs(text)

    # Phase 3: line-by-line block parsing
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # -- Code block placeholder --
        if line.strip().startswith("@@CODEBLOCK"):
            m = re.search(r"\d+", line.strip())
            if m:
                idx = int(m[0])
                if idx < len(code_blocks):
                    blocks.append(code_blocks[idx])
            i += 1
            continue

        # -- Blank line: skip --
        if line.strip() == "":
            i += 1
            continue

        # -- Horizontal rule --
        stripped = line.strip()
        if re.match(r"^-{3,}\s*$", stripped) or re.match(r"^\*{3,}\s*$", stripped) or re.match(r"^_{3,}\s*$", stripped):
            blocks.append(HorizontalRule())
            i += 1
            continue

        # -- Heading --
        heading_match = re.match(r"^(#{1,6})\s+(.*?)(?:\s+#*)?$", line)
        if heading_match:
            level = len(heading_match.group(1))
            blocks.append(Heading(level=level, text=heading_match.group(2).strip()))
            i += 1
            continue

        # -- Block quote (consecutive lines starting with >) --
        if line.lstrip().startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                # Strip the leading '> ' or '>'
                quote_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append(BlockQuote(text="\n".join(quote_lines).strip()))
            continue

        # -- Unordered list (lines starting with optional whitespace + -) --
        if re.match(r"^[ \t]*-(?!-{2,})", line):
            list_lines: list[str] = []
            while i < len(lines):
                ln = lines[i]
                # Part of the list: starts with - or is indented continuation
                if re.match(r"^[ \t]*-(?!-{2,})", ln):
                    list_lines.append(ln)
                    i += 1
                elif ln.strip() == "":
                    # Blank line ends the list
                    break
                elif ln.startswith(" ") or ln.startswith("\t"):
                    # Indented continuation
                    list_lines.append(ln)
                    i += 1
                else:
                    break
            raw_list = "\n".join(list_lines)
            blocks.append(_parse_unordered_list(raw_list))
            continue

        # -- Ordered list (lines starting with optional whitespace + digit.) --
        if re.match(r"^[ \t]*\d+\.", line):
            list_lines_o: list[str] = []
            while i < len(lines):
                ln = lines[i]
                if re.match(r"^[ \t]*\d+\.", ln):
                    list_lines_o.append(ln)
                    i += 1
                elif ln.strip() == "":
                    break
                elif ln.startswith(" ") or ln.startswith("\t"):
                    list_lines_o.append(ln)
                    i += 1
                else:
                    break
            raw_list_o = "\n".join(list_lines_o)
            blocks.append(_parse_ordered_list(raw_list_o))
            continue

        # -- Table --
        if "|" in line and i + 1 < len(lines):
            # Check if next line is a valid alignment row
            next_line = lines[i+1]
            if re.match(r"^[ \t]*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)+\|?[ \t]*$", next_line):
                headers = _parse_table_row(line)
                alignments = _parse_table_alignment(next_line, len(headers.cells))
                i += 2
                rows: list[TableRow] = []
                while i < len(lines):
                    ln = lines[i].strip()
                    if not ln or "|" not in ln:
                        break
                    rows.append(_parse_table_row(ln))
                    i += 1
                blocks.append(Table(alignments=alignments, headers=headers, rows=rows))
                continue

        # -- Paragraph: collect consecutive non-blank, non-special lines --
        para_lines: list[str] = []
        while i < len(lines):
            ln = lines[i]
            if ln.strip() == "":
                break
            # Stop if next line is a special block start
            if (re.match(r"^#{1,6}\s+", ln)
                    or re.match(r"^-{3,}\s*$", ln.strip())
                    or re.match(r"^\*{3,}\s*$", ln.strip())
                    or re.match(r"^_{3,}\s*$", ln.strip())
                    or ln.lstrip().startswith(">")
                    or re.match(r"^[ \t]*-(?!-{2,})", ln)
                    or re.match(r"^[ \t]*\d+\.", ln)
                    or ln.strip().startswith("@@CODEBLOCK")):
                # Only break if we already have content
                if para_lines:
                    break
                # Otherwise this shouldn't happen (handled above), but just in case
                break
            para_lines.append(ln)
            i += 1
        if para_lines:
            blocks.append(Paragraph(text="\n".join(para_lines)))

    # Append footnote definitions (renderer resolves them)
    for fndef in footnote_defs:
        blocks.append(fndef)

    return blocks


# -- Extraction helpers -------------------------------------------------------


def _extract_code_blocks(text: str) -> tuple[str, list[CodeBlock]]:
    """Extract fenced code blocks and replace with placeholders."""
    code_blocks: list[CodeBlock] = []
    matches = list(re.finditer(r"```((.|\n)*?)```", text, flags=re.M))

    for i, m in enumerate(matches):
        full_match = m[0]

        # Extract language hint
        lang_match = re.search(r"```([^\n]*)\n", full_match)
        lang = lang_match.group(1).strip() if lang_match else None
        if lang == "":
            lang = None

        # Extract code body
        body_match = re.sub(r"```.*?\n", "", full_match, count=1, flags=re.M)
        body = re.sub(r"```\s*$", "", body_match, flags=re.M)

        # Validate language against minted
        if lang is not None and lang not in languages:
            lang = None

        code_blocks.append(CodeBlock(code=body, language=lang))
        text = text.replace(full_match, f"@@CODEBLOCK{i}@@", 1)

    return text, code_blocks


def _extract_footnote_defs(text: str) -> tuple[str, list[FootnoteDef]]:
    """Extract footnote definitions and remove them from the text."""
    footnote_defs: list[FootnoteDef] = []
    matches = list(re.finditer(
        r"^\[\^(\d+)\]:\s*(.+(?:\n(?!\[\^).+)*)$", text, flags=re.M
    ))

    for m in matches:
        key = m.group(1)
        content = re.sub(r"\s+", " ", m.group(2)).strip()
        if content:
            footnote_defs.append(FootnoteDef(key=key, text=content))
        text = text.replace(m[0], "", 1)

    return text, footnote_defs


# -- List parsing -------------------------------------------------------------


def _parse_unordered_list(raw: str) -> ListBlock:
    """Parse a raw unordered list block into a ``ListBlock`` node."""
    # Collapse continuation lines (lines that don't start with -)
    collapsed = re.sub(r"\n(?!\s*-)", " ", raw, flags=re.M)
    items_data = process_list_indentation(collapsed)
    items = _build_list_items(items_data, ordered=False)
    return ListBlock(ordered=False, items=items)


def _parse_ordered_list(raw: str) -> ListBlock:
    """Parse a raw ordered list block into a ``ListBlock`` node."""
    # Collapse continuation lines
    collapsed = re.sub(r"\n(?!\s*\d+\.)", " ", raw, flags=re.M)

    # Parse items with indentation
    items_raw: list[list] = []
    firstindent = len(re.search(r"^\s*", collapsed)[0])  # type: ignore[index]
    for item in re.split(r"\n", collapsed):
        indent = len(re.search(r"^\s*", item)[0]) - firstindent  # type: ignore[index]
        content = re.sub(r"^\s*\d+\.\s*", "", item)
        items_raw.append([content, max(indent, 0)])

    # Normalize indentation levels
    if len({li[1] for li in items_raw}) > 1:
        mult = next((li[1] for li in items_raw if li[1] != 0), 1)
        for li in items_raw:
            if mult > 0 and int(li[1] / mult) == li[1] / mult:
                li[1] = int(li[1] / mult)
            else:
                li[1] = 0
        prev = 0
        for li in items_raw:
            if li[1] > prev + 1:
                li[1] = prev + 1
            prev = li[1]

    items = _build_list_items(items_raw, ordered=True)
    return ListBlock(ordered=True, items=items)


def _build_list_items(items_data: list[list], ordered: bool) -> list[ListItem]:
    """Build a nested ``ListItem`` tree from flat ``[text, level]`` pairs."""
    if not items_data:
        return []

    root_items: list[ListItem] = []
    stack: list[tuple[int, ListItem]] = []

    for text, level in items_data:
        item = ListItem(text=text)

        if level == 0:
            root_items.append(item)
            stack = [(0, item)]
        else:
            # Find the parent at level - 1
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack:
                parent = stack[-1][1]
                if parent.children is None:
                    parent.children = ListBlock(ordered=ordered, items=[])
                parent.children.items.append(item)

            stack.append((level, item))

    return root_items


# -- Table parsing ------------------------------------------------------------


def _parse_table_row(row: str) -> TableRow:
    """Parse a Markdown table row into cells, stripping outer pipes."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]

    # Split by '|' but try not to split by escaped '\|' (though GFM usually doesn't escape in standard markdown, simple split is enough for now)
    cells = [c.strip() for c in re.split(r"(?<!\\)\|", row)]
    return TableRow(cells=cells)


def _parse_table_alignment(row: str, num_cols: int) -> list[str]:
    """Parse a Markdown table alignment row into LaTeX alignments ('l', 'c', 'r')."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]

    parts = [p.strip() for p in row.split("|")]
    alignments: list[str] = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        left = part.startswith(":")
        right = part.endswith(":")

        if left and right:
            alignments.append("c")
        elif right:
            alignments.append("r")
        else:
            alignments.append("l")

    # Pad or truncate to match headers length
    if len(alignments) < num_cols:
        alignments.extend(["l"] * (num_cols - len(alignments)))
    return alignments[:num_cols]
