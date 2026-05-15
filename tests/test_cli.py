"""CLI integration tests using Click's CliRunner."""

from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from md2tex.cli import md2tex

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "markdown"


class TestCLIBasic:
    """Test basic CLI invocation."""

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(md2tex, ["--help"])
        assert result.exit_code == 0
        assert "Convert a Markdown file to a TeX file" in result.output

    def test_basic_conversion(self, tmp_path: Path) -> None:
        md_file = FIXTURES_DIR / "headings.md"
        out_file = tmp_path / "headings.tex"
        runner = CliRunner()
        result = runner.invoke(md2tex, [str(md_file), "-o", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert r"\subsection{" in content

    def test_complete_tex_file(self, tmp_path: Path) -> None:
        md_file = FIXTURES_DIR / "headings.md"
        out_file = tmp_path / "headings_complete.tex"
        runner = CliRunner()
        result = runner.invoke(md2tex, [str(md_file), "-c", "-o", str(out_file)])
        assert result.exit_code == 0
        content = out_file.read_text()
        assert r"\documentclass" in content
        assert r"\begin{document}" in content
        assert r"\end{document}" in content

    def test_complete_tex_file_listings_backend(self, tmp_path: Path) -> None:
        md_file = FIXTURES_DIR / "code_blocks.md"
        out_file = tmp_path / "code_listings.tex"
        runner = CliRunner()
        result = runner.invoke(
            md2tex,
            [str(md_file), "-c", "--code-backend", "listings", "-o", str(out_file)],
        )
        assert result.exit_code == 0
        content = out_file.read_text()
        assert r"\begin{lstlisting}" in content
        assert r"\begin{minted}" not in content

    def test_unnumbered_headers(self, tmp_path: Path) -> None:
        md_file = FIXTURES_DIR / "headings.md"
        out_file = tmp_path / "headings_unnumbered.tex"
        runner = CliRunner()
        result = runner.invoke(md2tex, [str(md_file), "-u", "-o", str(out_file)])
        assert result.exit_code == 0
        content = out_file.read_text()
        assert r"\subsection*{" in content

    def test_book_document_class(self, tmp_path: Path) -> None:
        md_file = FIXTURES_DIR / "headings.md"
        out_file = tmp_path / "headings_book.tex"
        runner = CliRunner()
        result = runner.invoke(md2tex, [str(md_file), "-d", "book", "-o", str(out_file)])
        assert result.exit_code == 0
        content = out_file.read_text()
        assert r"\section{" in content

    def test_french_quotes(self, tmp_path: Path) -> None:
        md_file = tmp_path / "quotes.md"
        md_file.write_text('He said "hello" to them.\n')
        out_file = tmp_path / "quotes.tex"
        runner = CliRunner()
        result = runner.invoke(md2tex, [str(md_file), "-f", "-o", str(out_file)])
        assert result.exit_code == 0
        content = out_file.read_text()
        assert r"\enquote{" in content


class TestCLIErrors:
    """Test CLI error handling."""

    def test_non_md_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(md2tex, ["file.txt"])
        assert result.exit_code != 0

    def test_nonexistent_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(md2tex, ["nonexistent.md"])
        assert result.exit_code != 0

    def test_default_output_dir_created(self, tmp_path: Path) -> None:
        """Verify the output/ directory is created when no -o is given."""
        md_file = FIXTURES_DIR / "headings.md"
        runner = CliRunner()
        # Run from tmp_path so the output/ dir is created there
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(md2tex, [str(md_file)])
            assert result.exit_code == 0
            assert (tmp_path / "output" / "headings.tex").exists()
        finally:
            os.chdir(original_dir)
