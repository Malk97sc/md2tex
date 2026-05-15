"""Snapshot-based regression tests for md2tex conversion.

Each test reads a Markdown fixture, runs it through the conversion
pipeline, and compares the output against the expected TeX snapshot.
"""

from __future__ import annotations

import pytest

from conftest import MARKDOWN_DIR, TEX_DIR, convert_markdown

# Collect all fixture names dynamically
FIXTURE_NAMES = sorted(p.stem for p in MARKDOWN_DIR.glob("*.md"))


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
def test_snapshot_article_numbered(fixture_name: str) -> None:
    """Verify conversion matches the TeX snapshot (article, numbered)."""
    md_path = MARKDOWN_DIR / f"{fixture_name}.md"
    tex_path = TEX_DIR / f"{fixture_name}.tex"

    md_content = md_path.read_text()
    expected = tex_path.read_text()
    result = convert_markdown(md_content)

    assert result == expected, (
        f"Snapshot mismatch for {fixture_name}.\n"
        f"--- Expected ---\n{expected[:500]}\n"
        f"--- Got ---\n{result[:500]}"
    )


class TestHeadings:
    """Test heading conversion for different document classes and numbering."""

    def test_article_numbered(self) -> None:
        md = "# Title\n\n## Subtitle\n"
        result = convert_markdown(md, document_class="article", unnumbered=False)
        assert r"\section{" in result
        assert r"\subsection{" in result

    def test_article_unnumbered(self) -> None:
        md = "# Title\n\n## Subtitle\n"
        result = convert_markdown(md, document_class="article", unnumbered=True)
        assert r"\section*{" in result
        assert r"\addcontentsline" in result

    def test_book_numbered(self) -> None:
        md = "# Title\n\n## Subtitle\n"
        result = convert_markdown(md, document_class="book", unnumbered=False)
        assert r"\chapter{" in result
        assert r"\section{" in result

    def test_book_unnumbered(self) -> None:
        md = "# Title\n\n## Subtitle\n"
        result = convert_markdown(md, document_class="book", unnumbered=True)
        assert r"\chapter*{" in result
        assert r"\addcontentsline" in result


class TestInlineFormatting:
    """Test inline formatting conversions."""

    def test_bold(self) -> None:
        result = convert_markdown("**bold text**\n")
        assert r"\textbf{" in result

    def test_italic(self) -> None:
        result = convert_markdown("*italic text*\n")
        assert r"\textit{" in result

    def test_inline_code(self) -> None:
        result = convert_markdown("`code`\n")
        assert r"\texttt{" in result


class TestQuotes:
    """Test quote conversions."""

    def test_block_quote(self) -> None:
        md = "> This is a quote.\n> Second line.\n"
        result = convert_markdown(md)
        assert r"\begin{quotation}" in result
        assert r"\end{quotation}" in result

    def test_inline_quote_anglosaxon(self) -> None:
        md = 'He said "hello" to them.\n'
        result = convert_markdown(md, french_quote=False)
        assert "``" in result

    def test_inline_quote_french(self) -> None:
        md = 'He said "hello" to them.\n'
        result = convert_markdown(md, french_quote=True)
        assert r"\enquote{" in result


class TestLists:
    """Test list conversions."""

    def test_unordered_flat(self) -> None:
        md = "- Item 1\n- Item 2\n"
        result = convert_markdown(md)
        assert r"\begin{itemize}" in result
        assert r"\item" in result
        assert r"\end{itemize}" in result

    def test_unordered_nested(self) -> None:
        md = "- Item 1\n  - Nested item\n- Item 2\n"
        result = convert_markdown(md)
        # Should have nested itemize
        count = result.count(r"\begin{itemize}")
        assert count >= 2


class TestCodeBlocks:
    """Test code block conversions."""

    def test_code_with_language(self) -> None:
        md = "```python\nprint('hi')\n```\n"
        result = convert_markdown(md)
        assert r"\begin{listing}" in result
        assert r"\begin{minted}{python}" in result

    def test_code_without_language(self) -> None:
        md = "```\nplain code\n```\n"
        result = convert_markdown(md)
        assert r"\begin{lstlisting}" in result


class TestLinks:
    """Test link and image conversions."""

    def test_hyperlink(self) -> None:
        md = "[Example](https://example.com)\n"
        result = convert_markdown(md)
        assert r"\href{" in result

    def test_image(self) -> None:
        md = "![Alt text](image.png)\n"
        result = convert_markdown(md)
        assert r"\begin{figure}" in result
        assert r"\includegraphics" in result
        assert r"\caption{" in result


class TestSeparators:
    """Test separator conversions."""

    def test_horizontal_rule(self) -> None:
        md = "Text\n\n---\n\nMore text\n"
        result = convert_markdown(md)
        assert r"\rule{\linewidth}" in result

    def test_html_break(self) -> None:
        md = "Line one<br>Line two\n"
        result = convert_markdown(md)
        # <br> should be replaced with newlines
        assert "<br>" not in result


class TestFootnotes:
    """Test footnote conversions."""

    def test_basic_footnote(self) -> None:
        md = "Text with a footnote [^1] here.\n\n[^1]: The footnote content.\n"
        result = convert_markdown(md)
        assert r"\footnote{" in result

    def test_loose_footnote_cleaned(self) -> None:
        md = "Text with a loose pointer [^99] here.\n"
        result = convert_markdown(md)
        # Loose pointers should be deleted
        assert "[^99]" not in result
        assert r"\footnote{" not in result


class TestTables:
    """Test GFM table conversions."""

    def test_basic_table(self) -> None:
        md = "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
        result = convert_markdown(md)
        assert r"\begin{table}[h!]" in result
        assert r"\begin{tabular}{ l | l }" in result
        assert r"\textbf{A} & \textbf{B} \\" in result
        assert r"\hline" in result
        assert r"1 & 2 \\" in result


class TestStrikethrough:
    """Test strikethrough inline conversions."""

    def test_basic_strikethrough(self) -> None:
        md = "Text with ~~strikethrough~~ here.\n"
        result = convert_markdown(md)
        assert r"\sout{strikethrough}" in result
