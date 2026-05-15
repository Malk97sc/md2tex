import re

from .helpers import process_list_indentation
from .minted import languages

# ---------------------------------------------------------------
# Regex-based conversion from Markdown to LaTeX.
# Main functions for the conversion process.
# Functions are organized into classes for clarity.
# ---------------------------------------------------------------


class MDSimple:
    """Simple substitutions using a regex-to-replacement mapping.

    ``simple_sub`` maps regular expressions to their replacements,
    used with ``re.sub``. Only for simple Markdown elements like
    ``*``, `` ` ``, etc.
    """

    simple_sub = {
        # code, bold, italics
        r"(?<!\*)\*{2}(?!\*)(.+?)(?<!\*)\*{2}(?!\*)": r"\\textbf{\1}",  # bold
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)": r"\\textit{\1}",  # italics
        r"(?<!`)`(?!`)(.+?)(?<!`)`(?!`)": r"\\texttt{\1}",  # inline code

        # images and hyperlink
        r"(?<!!)\[(.*?)\]\((.*?)\)": r"\\href{\2}{\1}",  # hyperlink
        r"!\[(.*?)\]\((.*?)\)": r"""
\\begin{figure}[h!]
    \\centering
    \\includegraphics[width=\\linewidth]{\2}
    \\caption{\1}
\\end{figure}""",  # images

        # separators
        r"-{3,}": r"\\par\\noindent\\rule{\\linewidth}{0.4pt}",  # horizontal line
        r"<br/?>": "\n\n",  # line breaks
    }

    @staticmethod
    def convert(string: str) -> str:
        """Perform the conversion: replace Markdown syntax with TeX syntax.

        Parameters
        ----------
        string:
            The string representation of the Markdown file to convert.

        Returns
        -------
        str:
            String with the conversion performed.
        """
        for k, v in MDSimple.simple_sub.items():
            string = re.sub(k, v, string, flags=re.M)
        return string


class MDHeader:
    """Header substitutions.

    Contains mappings for converting Markdown headers to LaTeX headers
    for both ``book`` and ``article`` document classes, in numbered
    and unnumbered variants.
    """

    book_numbered = {
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\chapter{\2}\n",
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\section{\2}\n",
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": r"\\subsection{\2}\n",
        r"^\s*(\\#){4}(?!\\#?)(.*?)$": r"\\subsubsection{\2}\n",
        r"^\s*(\\#){5,}(?!\\#?)(.*?)$": r"\n\n\\textbf{\2}\n\n",
    }
    book_unnumbered = {
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\chapter*{\2}\n\\addcontentsline{toc}{chapter}{\2}\n",
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{section}{\2}\n",
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": r"\\subsection*{\2}\n\\addcontentsline{toc}{subsection}{\2}\n",
        r"^\s*(\\#){4}(?!\\#?)(.*?)$": (
            r"\\subsubsection*{\2}\n\\addcontentsline{toc}{subsubsection}{\2}\n"
        ),
        r"^\s*(\\#){5,}(?!\\#?)(.*?)$": r"\n\n\\noindent{}\textbf{\2}\n\n",
    }
    article_numbered = {
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\section{\2}\n",
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\subsection{\2}\n",
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": r"\\subsubsection{\2}\n",
        r"^\s*(\\#){4,}(?!\\#?)(.*?)$": r"\n\n\\noindent{}\\textbf{\2}\n\n",
    }
    article_unnumbered = {
        r"^\s*(\\#){1}(?!\\#?)(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{section}{\2}\n",
        r"^\s*(\\#){2}(?!\\#?)(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{subsection}{\2}\n",
        r"^\s*(\\#){3}(?!\\#?)(.*?)$": (
            r"\\subsection*{\2}\n\\addcontentsline{toc}{subsubsection}{\2}\n"
        ),
        r"^\s*(\\#){4,}(?!\\#?)(.*?)$": r"\n\n\\noindent{}\\textbf{\2}\n\n",
    }

    @staticmethod
    def convert(string: str, unnumbered: bool, document_class: str) -> str:
        """Replace Markdown titles with numbered or unnumbered LaTeX titles.

        Parameters
        ----------
        string:
            The Markdown representation of the string to convert.
        unnumbered:
            Flag indicating that the LaTeX headers should be unnumbered.
        document_class:
            The class to convert the document to (``article`` or ``book``).

        Returns
        -------
        str:
            Processed string.
        """
        if unnumbered is True:
            if document_class == "article":
                substitute = MDHeader.article_unnumbered
            else:
                substitute = MDHeader.book_unnumbered
        else:
            if document_class == "article":
                substitute = MDHeader.article_numbered
            else:
                substitute = MDHeader.book_numbered
        for k, v in substitute.items():
            string = re.sub(k, v, string, flags=re.M)
        return string


class MDQuote:
    """Inline and block quote substitution.

    Contains methods for replacing multiline Markdown quotes (``>``)
    into LaTeX ``\\quote{}`` and converting inline quotes to LaTeX
    french or anglo-saxon quotes.
    """

    @staticmethod
    def block_quote(string: str) -> str:
        """Replace Markdown block quotes ``>`` with LaTeX ``\\begin{quotation}``.

        Works in multiline mode.

        Parameters
        ----------
        string:
            The string representation of the Markdown file.

        Returns
        -------
        str:
            The updated string representation.
        """
        string = re.sub(
            r"^((>.+(\n|$))+)",
            r"\\begin{quotation} \n \1 \n \\end{quotation}",
            string, flags=re.M,
        ).replace(">", " ")
        return string

    @staticmethod
    def inline_quote(string: str, french_quote: bool) -> str:
        """Convert Markdown quotes to LaTeX quotes.

        Parameters
        ----------
        string:
            The string representation of the Markdown file.
        french_quote:
            Translate the quotes as french quotes (``\\enquote{}``)
            or anglo-saxon quotes (````''``).

        Returns
        -------
        str:
            The updated string representation.
        """
        if french_quote is True:
            string = re.sub(r"\"(.*)\"", r"\\enquote{\1}", string)
            string = re.sub(r"'(.*)'", r'``\1"', string)
        else:
            string = re.sub(r"\"(.*)\"", r'``\1"', string)
            string = re.sub(r"'(.*)'", r"`\1'", string)
        return string


class MDList:
    """List substitution: replace Markdown nested lists with LaTeX nested lists.

    Contains methods for creating LaTeX ``itemize`` and ``enumerate``
    environments from Markdown unordered and ordered lists.
    """

    @staticmethod
    def unordered_l(string: str) -> str:
        """Translate a Markdown unordered list into a LaTeX ``itemize`` environment.

        Parameters
        ----------
        string:
            The string representation of the Markdown file.

        Returns
        -------
        str:
            The updated string representation.
        """
        lists = re.finditer(r"((^[ \t]*?-(?!-{2,}).*?\n)+(.+\n)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            lstext = ls[0]
            string = string.replace(lstext, "@@LISTTOKEN@@")
            lstext = re.sub(r"\n(?!\s*-)", " ", lstext, flags=re.M)

            lsitems = process_list_indentation(lstext)

            items = ""
            prev = 0
            for li in lsitems:
                if li[1] - prev > 0:
                    items += "\\begin{itemize} \n \\item " * (li[1] - prev)
                    items += li[0] + "\n"
                elif li[1] - prev < 0:
                    items += "\\end{itemize}\n" * (prev - li[1])
                    items += "\\item " + li[0] + "\n"
                else:
                    items += "\\item " + li[0] + "\n"
                prev = li[1]

            items += "\\end{itemize}\n" * prev

            itemize = r"""
\begin{itemize}
@@ITEMTOKEN@@
\end{itemize}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", itemize)

        return string

    @staticmethod
    def ordered_l(string: str) -> str:
        """Translate a Markdown numbered list into a LaTeX ``enumerate`` environment.

        Parameters
        ----------
        string:
            The string representation of the Markdown file.

        Returns
        -------
        str:
            The updated string representation.
        """
        lists = re.finditer(r"((^[ \t]*?\d+\..*?\n?)+(.+\n?)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            lstext = ls[0]
            string = string.replace(lstext, "@@LISTTOKEN@@")
            lstext = re.sub(r"\n(?!\s*\d+\.)", " ", lstext, flags=re.M)

            lsitems = process_list_indentation(lstext)

            items = ""
            prev = 0
            for li in lsitems:
                if li[1] - prev > 0:
                    items += "\\begin{enumerate} \n \\item " * (li[1] - prev)
                    items += li[0] + "\n"
                elif li[1] - prev < 0:
                    items += "\\end{enumerate}\n" * (prev - li[1])
                    items += "\\item " + li[0] + "\n"
                else:
                    items += "\\item " + li[0] + "\n"
                prev = li[1]

            items += "\\end{itemize}\n" * prev

            enumerate_env = r"""
            \begin{enumerate}
            @@ITEMTOKEN@@
            \end{enumerate}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", enumerate_env)

        return string


class MDCode:
    """Block code substitution.

    Creates a LaTeX ``minted`` or ``lstlisting`` environment from a
    Markdown fenced code block.
    """

    @staticmethod
    def block_code(string: str) -> str:
        """Translate a Markdown code block into a ``minted`` or ``lstlisting`` block.

        If the code language is supported by minted/pygments, a ``minted``
        environment inside a ``listing`` environment is created. Otherwise,
        a plain ``lstlisting`` environment is used.

        Parameters
        ----------
        string:
            The string representation of the Markdown file.

        Returns
        -------
        str:
            The updated string representation.
        """
        matches = re.finditer(r"```((.|\n)*?)```", string, flags=re.M)
        for m in matches:
            code = m[0]
            string = string.replace(code, "@@MINTEDTOKEN@@")

            try:
                lang = re.search(r"```([^\n]*)$", code, flags=re.M)[0].replace("```", "").strip()  # type: ignore[index]
            except TypeError:
                lang = None

            if lang is not None and lang in languages:
                env = r"""
\begin{listing}[h!]
    \begin{minted}{@@LANGTOKEN@@}
@@CODETOKEN@@
    \end{minted}
\end{listing}"""
                code = re.sub(r"```.*?\n((.|\n)+?)```", r"\1", code, flags=re.M)
                code = env.replace("@@LANGTOKEN@@", lang).replace("@@CODETOKEN@@", code)
            else:
                env = r"""
\begin{lstlisting}
@@CODETOKEN@@
\end{lstlisting}
                """
                code = env.replace("@@CODETOKEN@@", re.sub(r"```", "", code, flags=re.M))

            string = string.replace("@@MINTEDTOKEN@@", code)

        return string


class MDReference:
    r"""Substitutions for references inside a Markdown document.

    Currently only handles footnote substitutions: replace Markdown
    footnotes (``[\^\d+]``) with LaTeX ``\footnote{}``.
    """

    @staticmethod
    def footnote(string: str) -> str:
        r"""Translate a Markdown footnote ``[^\d+]`` to a LaTeX ``\footnote{}``.

        Parameters
        ----------
        string:
            The string representation of a Markdown file.

        Returns
        -------
        str:
            The updated string representation.
        """
        footnotes = re.finditer(r"\[\\\^\d+\](?![ \t]*:)", string, flags=re.M)
        for match in footnotes:
            try:
                pointer = match[0]
                key = re.search(r"\d+", pointer)[0]  # type: ignore[index]
                fnote = re.search(
                    rf"(\[\\\^{re.escape(key)}\]:)(.+\n?)*",
                    string, flags=re.M,
                )
                texnote = re.sub(r"\s+", " ", fnote[0].replace(fnote[1], ""))  # type: ignore[index]

                if not re.search(r"^\s*$", texnote):
                    texnote = r"\footnote{" + texnote + "}"
                    string = string.replace(fnote[0], "")  # type: ignore[index]
                    string = string.replace(pointer, texnote)
                else:
                    string = string.replace(pointer, "")
                    string = string.replace(fnote[0], "")  # type: ignore[index]

            except TypeError:
                pass
        # delete all loose footnote strings
        string = re.sub(r"\[\\\^\d+\](?![ \t]*:)", "", string, flags=re.M)
        string = re.sub(r"(\[\\\^\d+\]:)(.+\n?)*", "", string, flags=re.M)

        return string


class MDCleaner:
    """Clean the input Markdown and output LaTeX.

    Contains methods to prepare Markdown by escaping special TeX characters
    and removing code blocks from the pipeline, and to clean the resulting
    TeX by reinserting escaped code blocks.
    """

    @staticmethod
    def prepare_markdown(string: str) -> tuple[str, dict[str, str]]:
        """Prepare Markdown for transformation.

        - Strip empty lines by removing inline spaces.
        - Escape LaTeX special characters.
        - Remove code blocks from the pipeline to avoid mangling their content.

        This function is used after ``block_code()`` to avoid replacing
        special characters that should be interpreted verbatim by LaTeX.

        Parameters
        ----------
        string:
            The string representation of a Markdown file.

        Returns
        -------
        tuple[str, dict[str, str]]:
            The updated string and a dictionary of escaped code blocks.
        """
        string = re.sub(r"^[ \t]*\n", r"\n\n", string, flags=re.M)
        string = string.replace("@@", "USERRESERVEDTOKEN")

        # Escape all code blocks so their content is not affected.
        codematch = re.finditer(
            r"\\begin\{(listing|lstlisting)}(.|\n)*?\\end\{(listing|lstlisting)}",
            string, flags=re.M,
        )
        codedict: dict[str, str] = {}
        for n, match in enumerate(codematch):
            block = match[0]
            string = string.replace(block, f"@@CODETOKEN{n}@@")
            codedict[f"@@CODETOKEN{n}@@"] = block

        string = string.replace(r"{", r"\{")
        string = string.replace(r"}", r"\}")
        string = re.sub(r"\\(?![{}])", r"\\textbackslash{}", string, flags=re.M)
        string = string.replace(r">", r"\textgreater{}")
        string = string.replace(r"#", r"\#")
        string = string.replace("$", r"\$")
        string = string.replace("%", r"\%")
        string = string.replace(r"$", r"\&")
        string = string.replace(r"~", r"\~")
        string = string.replace("_", r"\_")
        string = re.sub(r"\^", r"\\^", string, flags=re.M)

        return string, codedict

    @staticmethod
    def clean_tex(string: str, codedict: dict[str, str]) -> str:
        """Clean spaces around LaTeX commands and reinject escaped code blocks.

        Parameters
        ----------
        string:
            The string representation of the Markdown file.
        codedict:
            The dictionary containing escaped code blocks.

        Returns
        -------
        str:
            The cleaned string.
        """
        for k, v in codedict.items():
            string = string.replace(k, v)

        string = re.sub(r"((?<!^ ) )+", " ", string, flags=re.M)
        string = re.sub(r"{\s+", r"{", string, flags=re.M)
        string = re.sub(r"\s+}", r"}", string, flags=re.M)
        string = re.sub(r"\n{2,}", r"\n\n", string, flags=re.M)
        string = re.sub(r"(\\begin\{.*?)\n{2,}", r"\1\n", string, flags=re.M)
        string = re.sub(r"\n{2,}(\\end\{)", r"\n\1", string, flags=re.M)

        string = string.replace("USERRESERVEDTOKEN", "@@")

        return string
