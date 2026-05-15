"""TeX renderer for md2tex IR nodes.

Takes a :data:`~md2tex.nodes.Document` (a list of block-level nodes)
and renders it to a LaTeX string.  Inline formatting (bold, italic,
inline code, links, images) is applied as regex transforms on text
content after TeX escaping.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .escaping import escape_tex
from .nodes import (
    Block,
    BlockQuote,
    CodeBlock,
    Document,
    FootnoteDef,
    Heading,
    HorizontalRule,
    ListBlock,
    Paragraph,
    Table,
)


@dataclass
class RenderOptions:
    """Options controlling the TeX rendering."""

    document_class: str = "article"
    unnumbered: bool = False
    french_quote: bool = False
    code_backend: str = "auto"


def render_tex(document: Document, options: RenderOptions | None = None) -> str:
    """Render a parsed document to a TeX string.

    Parameters
    ----------
    document:
        The parsed IR document (list of blocks).
    options:
        Rendering options.

    Returns
    -------
    str:
        The rendered TeX string.
    """
    if options is None:
        options = RenderOptions()

    # Separate footnote definitions from blocks
    footnotes: dict[str, str] = {}
    blocks: list[Block] = []
    for node in document:
        if isinstance(node, FootnoteDef):
            footnotes[node.key] = node.text
        else:
            blocks.append(node)

    parts: list[str] = []
    for block in blocks:
        rendered = _render_block(block, options, footnotes)
        if rendered is not None:
            parts.append(rendered)

    result = "\n\n".join(parts)

    # Clean up excessive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    # Ensure trailing newline
    if result and not result.endswith("\n"):
        result += "\n"

    return result


def _render_block(
    block: Block, options: RenderOptions, footnotes: dict[str, str]
) -> str | None:
    """Render a single block node."""
    if isinstance(block, Heading):
        return _render_heading(block, options)
    if isinstance(block, Paragraph):
        return _render_paragraph(block, options, footnotes)
    if isinstance(block, CodeBlock):
        return _render_code_block(block, options)
    if isinstance(block, BlockQuote):
        return _render_block_quote(block, options, footnotes)
    if isinstance(block, ListBlock):
        return _render_list_block(block, options, footnotes)
    if isinstance(block, Table):
        return _render_table(block, options, footnotes)
    if isinstance(block, HorizontalRule):
        return r"\par\noindent\rule{\linewidth}{0.4pt}"
    return None


# -- Heading ------------------------------------------------------------------

# Mapping: (document_class, unnumbered) -> {level: command}
_HEADING_COMMANDS: dict[tuple[str, bool], dict[int, str]] = {
    ("article", False): {
        1: r"\section{%s}",
        2: r"\subsection{%s}",
        3: r"\subsubsection{%s}",
    },
    ("article", True): {
        1: r"\section*{%s}" + "\n" + r"\addcontentsline{toc}{section}{%s}",
        2: r"\subsection*{%s}" + "\n" + r"\addcontentsline{toc}{subsection}{%s}",
        3: r"\subsubsection*{%s}" + "\n" + r"\addcontentsline{toc}{subsubsection}{%s}",
    },
    ("book", False): {
        1: r"\chapter{%s}",
        2: r"\section{%s}",
        3: r"\subsection{%s}",
        4: r"\subsubsection{%s}",
    },
    ("book", True): {
        1: r"\chapter*{%s}" + "\n" + r"\addcontentsline{toc}{chapter}{%s}",
        2: r"\section*{%s}" + "\n" + r"\addcontentsline{toc}{section}{%s}",
        3: r"\subsection*{%s}" + "\n" + r"\addcontentsline{toc}{subsection}{%s}",
        4: r"\subsubsection*{%s}" + "\n" + r"\addcontentsline{toc}{subsubsection}{%s}",
    },
}


def _render_heading(heading: Heading, options: RenderOptions) -> str:
    """Render a heading node."""
    text = escape_tex(heading.text)
    commands = _HEADING_COMMANDS.get((options.document_class, options.unnumbered), {})
    max_level = max(commands) if commands else 3

    if heading.level <= max_level:
        template = commands[heading.level]
        # Templates with %s get the text inserted
        return template.replace("%s", text)

    # Levels beyond the max: render as bold text
    if options.unnumbered:
        return rf"\noindent{{}}\textbf{{{text}}}"
    return rf"\textbf{{{text}}}"


# -- Paragraph ---------------------------------------------------------------


def _render_paragraph(
    para: Paragraph, options: RenderOptions, footnotes: dict[str, str]
) -> str:
    """Render a paragraph with inline formatting and footnote resolution."""
    text = para.text
    text = escape_tex(text)
    text = _resolve_footnotes(text, footnotes)
    text = _apply_inline_formatting(text, options)
    return text


# -- Code block ---------------------------------------------------------------


def _render_code_block(block: CodeBlock, options: RenderOptions) -> str:
    """Render a code block.  Content is NOT escaped."""
    if options.code_backend not in {"auto", "minted", "listings"}:
        raise ValueError(f"Unsupported code backend `{options.code_backend}`")

    use_minted = (
        options.code_backend == "minted"
        or (options.code_backend == "auto" and block.language is not None)
    )

    if use_minted and block.language is not None:
        return (
            "\\begin{listing}[h!]\n"
            f"    \\begin{{minted}}{{{block.language}}}\n"
            f"{block.code}"
            "    \\end{minted}\n"
            "\\end{listing}"
        )
    return (
        "\\begin{lstlisting}\n"
        f"{block.code}"
        "\\end{lstlisting}"
    )


# -- Block quote --------------------------------------------------------------


def _render_block_quote(
    quote: BlockQuote, options: RenderOptions, footnotes: dict[str, str]
) -> str:
    """Render a block quote."""
    text = quote.text
    text = escape_tex(text)
    text = _resolve_footnotes(text, footnotes)
    text = _apply_inline_formatting(text, options)
    return f"\\begin{{quotation}}\n{text}\n\\end{{quotation}}"


# -- Lists --------------------------------------------------------------------


def _render_list_block(
    block: ListBlock, options: RenderOptions, footnotes: dict[str, str],
    indent: int = 0,
) -> str:
    """Render a list block (recursive for nested lists)."""
    env = "enumerate" if block.ordered else "itemize"
    prefix = "    " * indent

    lines: list[str] = [f"{prefix}\\begin{{{env}}}"]
    for item in block.items:
        text = escape_tex(item.text)
        text = _resolve_footnotes(text, footnotes)
        text = _apply_inline_formatting(text, options)
        lines.append(f"{prefix}    \\item {text}")
        if item.children is not None:
            nested = _render_list_block(item.children, options, footnotes, indent + 1)
            lines.append(nested)
    lines.append(f"{prefix}\\end{{{env}}}")

    return "\n".join(lines)


# -- Table --------------------------------------------------------------------


def _render_table(
    table: Table, options: RenderOptions, footnotes: dict[str, str]
) -> str:
    """Render a GFM table into a LaTeX tabular environment."""
    # Build column alignment string (e.g., 'l | c | r')
    align_str = " | ".join(table.alignments)

    lines: list[str] = []
    lines.append("\\begin{table}[h!]")
    lines.append("    \\centering")
    lines.append(f"    \\begin{{tabular}}{{ {align_str} }}")

    # Render headers
    header_cells = []
    for cell in table.headers.cells:
        text = escape_tex(cell)
        text = _resolve_footnotes(text, footnotes)
        text = _apply_inline_formatting(text, options)
        header_cells.append(f"\\textbf{{{text}}}")
    lines.append("        " + " & ".join(header_cells) + " \\\\")
    lines.append("        \\hline")

    # Render rows
    for row in table.rows:
        row_cells = []
        for cell in row.cells:
            text = escape_tex(cell)
            text = _resolve_footnotes(text, footnotes)
            text = _apply_inline_formatting(text, options)
            row_cells.append(text)
        lines.append("        " + " & ".join(row_cells) + " \\\\")

    lines.append("    \\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


# -- Footnotes ----------------------------------------------------------------


def _resolve_footnotes(text: str, footnotes: dict[str, str]) -> str:
    """Replace ``[^N]`` references with ``\\footnote{content}``.

    Unresolved references are silently removed.
    """
    def _replace_ref(m: re.Match) -> str:  # type: ignore[type-arg]
        key = m.group(1)
        if key in footnotes:
            content = escape_tex(footnotes[key])
            content = _apply_inline_formatting(content, RenderOptions())
            return rf"\footnote{{{content}}}"
        return ""

    # The text has already been passed through `escape_tex`, so `^` is `\^{}`
    text = re.sub(r"\[\\\^\{\}(\d+)\]", _replace_ref, text)
    return text


# -- Inline formatting -------------------------------------------------------


def _apply_inline_formatting(text: str, options: RenderOptions) -> str:
    """Apply inline Markdown formatting as regex substitutions.

    This runs on *already TeX-escaped* text, so the regexes match
    the escaped forms of Markdown markers.
    """
    # Bold: **text**  (after escaping, * is still *)
    text = re.sub(r"(?<!\*)\*{2}(?!\*)(.+?)(?<!\*)\*{2}(?!\*)", r"\\textbf{\1}", text)
    # Italic: *text*
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\\textit{\1}", text)
    # Strikethrough: ~~text~~ (escaped as \~{}\~{})
    text = re.sub(r"\\~\{\}\\~\{\}(.*?)\\~\{\}\\~\{\}", r"\\sout{\1}", text)
    # Inline code: `text`
    text = re.sub(r"(?<!`)`(?!`)(.+?)(?<!`)`(?!`)", r"\\texttt{\1}", text)
    # Images: ![alt](url) -- must come before hyperlinks
    text = re.sub(
        r"!\[(.*?)\]\((.*?)\)",
        (
            "\n\\\\begin{figure}[h!]\n"
            "    \\\\centering\n"
            "    \\\\includegraphics[width=\\\\linewidth]{\\2}\n"
            "    \\\\caption{\\1}\n"
            "\\\\end{figure}"
        ),
        text,
    )
    # Hyperlinks: [text](url)
    text = re.sub(r"(?<!!)\[(.*?)\]\((.*?)\)", r"\\href{\2}{\1}", text)
    # HTML line breaks
    text = re.sub(r"<br/?>", "\n\n", text)
    # Inline quotes
    text = _apply_inline_quotes(text, options.french_quote)

    return text


def _apply_inline_quotes(text: str, french_quote: bool) -> str:
    """Convert inline quotes to TeX."""
    if french_quote:
        text = re.sub(r"\"(.*)\"", r"\\enquote{\1}", text)
        text = re.sub(r"'(.*)'", r"``\1\"", text)
    else:
        text = re.sub(r"\"(.*)\"", r"``\1\"", text)
        text = re.sub(r"'(.*)'", r"`\1'", text)
    return text
