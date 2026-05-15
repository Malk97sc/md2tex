"""TeX special-character escaping.

Extracted from the old ``MDCleaner.prepare_markdown`` and rewritten to
fix the ordering bugs that corrupted ``$`` and prevented block-quote
matching.

The key insight is that escaping must happen *after* block-level
extraction (code blocks, block quotes, headings, lists) so that
Markdown-significant characters are not destroyed before parsing.
"""

from __future__ import annotations

import re

# Characters that have special meaning in TeX and must be escaped
# when they appear in regular text content.  The order matters:
# backslash must be escaped first (it is the escape character itself),
# and braces must be handled before other replacements that produce
# braces.
_TEX_ESCAPES: list[tuple[str, str]] = [
    # Backslash must come first.  We turn a literal ``\`` into
    # ``\textbackslash{}``, but we must not touch backslashes that were
    # already part of our own TeX output.  Since escaping now runs on
    # *parsed text content* rather than the full mixed string, every ``\``
    # at this point is genuinely a user backslash.
    ("\\", r"\textbackslash{}"),
    # Braces
    ("{", r"\{"),
    ("}", r"\}"),
    # Other specials (order does not matter among these)
    ("#", r"\#"),
    ("$", r"\$"),
    ("%", r"\%"),
    ("&", r"\&"),
    ("~", r"\~{}"),
    ("_", r"\_"),
    ("^", r"\^{}"),
]


def escape_tex(text: str) -> str:
    """Escape TeX special characters in *text*.

    This should only be called on text content that is **not** inside
    a verbatim / code environment.

    Parameters
    ----------
    text:
        Raw text that may contain TeX specials.

    Returns
    -------
    str:
        Text with all specials properly escaped.
    """
    for char, replacement in _TEX_ESCAPES:
        text = text.replace(char, replacement)
    return text


def normalize_blank_lines(text: str) -> str:
    """Collapse whitespace-only lines into single blank lines.

    Parameters
    ----------
    text:
        Raw Markdown text.

    Returns
    -------
    str:
        Text with whitespace-only lines normalized to ``\\n\\n``.
    """
    return re.sub(r"^[ \t]*\n", "\n\n", text, flags=re.M)
