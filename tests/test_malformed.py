"""Tests for malformed and edge-case Markdown inputs."""

from __future__ import annotations

import pytest

from conftest import convert_markdown
from md2tex.errors_warnings import IndentationException


class TestMalformedInput:
    """Test handling of malformed Markdown."""

    def test_empty_input(self) -> None:
        """Empty input should produce empty-ish output without crashing."""
        result = convert_markdown("")
        assert isinstance(result, str)

    def test_only_whitespace(self) -> None:
        """Whitespace-only input should not crash."""
        result = convert_markdown("   \n\n  \n")
        assert isinstance(result, str)

    def test_unclosed_code_block(self) -> None:
        """Unclosed code block should not crash (may produce partial output)."""
        md = "```python\ndef foo():\n    pass\n"
        result = convert_markdown(md)
        assert isinstance(result, str)

    def test_inconsistent_list_indentation(self) -> None:
        """Inconsistent indentation should raise IndentationException."""
        md = "  - First item\n  - Second item\n- Less indented item\n"
        with pytest.raises(IndentationException):
            convert_markdown(md)

    def test_loose_footnote_pointer(self) -> None:
        """Loose footnote pointer (no matching footnote) should be deleted."""
        md = "Text with pointer [^42] and nothing else.\n"
        result = convert_markdown(md)
        assert "[^42]" not in result
        assert r"\footnote" not in result

    def test_loose_footnote_body(self) -> None:
        """Footnote body with no pointer in text should be deleted."""
        md = "Some text.\n\n[^7]: Orphan footnote body.\n"
        result = convert_markdown(md)
        assert "[^7]" not in result

    def test_special_characters(self) -> None:
        """TeX special characters should be escaped."""
        md = "Price is 20% off ~ sale.\n"
        result = convert_markdown(md)
        assert r"\%" in result

    def test_single_line_no_newline(self) -> None:
        """Single line without trailing newline should still convert."""
        md = "Just some text"
        result = convert_markdown(md)
        assert "Just some text" in result

    def test_deeply_nested_list(self) -> None:
        """Deeply nested list should not crash."""
        md = (
            "- Level 0\n"
            "  - Level 1\n"
            "    - Level 2\n"
            "      - Level 3\n"
        )
        result = convert_markdown(md)
        assert r"\begin{itemize}" in result
