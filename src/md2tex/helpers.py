import re

from .errors_warnings import IndentationException


def process_list_indentation(lstext: str) -> list[list]:
    """Process indentation levels to build nested LaTeX list environments.

    Represent the markdown list as a list of ``[item_content, indentation_level]``
    pairs, validate the indentation, and replace absolute space counts with
    normalized nesting levels.

    Rules
    -----
    - All items must be at least as indented as the first list item.
    - Indentation levels must be multiples of the first nested item's indent.
    - An item cannot skip a nesting level; if it does, the level is reset.

    Parameters
    ----------
    lstext:
        String representation of a markdown list (ordered or unordered).

    Returns
    -------
    list[list]:
        ``[[item_content, indentation_level], ...]``
    """
    lsitems: list[list] = []  # [item content, indentation level]
    firstindent = len(re.search(r"^\s*", lstext)[0])  # type: ignore[index]
    for item in re.split(r"\n", lstext):
        indent = len(re.search(r"^\s*", item)[0]) - firstindent  # type: ignore[index]
        if indent < 0:
            raise IndentationException(key="firstindent", lstext=lstext)
        else:
            lsitems.append([
                re.sub(r"^\s*-\s*", "", item),  # item content
                indent,  # indentation (number of spaces)
            ])

    # If there are different indentation levels:
    # - check that all levels have a common multiplier
    # - replace absolute space counts by indentation levels
    # - correct any skipped indentation levels
    if len({li[1] for li in lsitems}) > 1:
        mult = next((li[1] for li in lsitems if li[1] != 0), 0)

        for li in lsitems:
            if int(li[1] / mult) == li[1] / mult:
                li[1] = int(li[1] / mult)
            else:
                raise IndentationException(key="multiplier", lstext=lstext)

        prev = 0
        for li in lsitems:
            if li[1] > prev + 1:
                li[1] = prev + 1
            prev = li[1]

    return lsitems
