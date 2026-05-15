"""md2tex services layer -- encapsulates core text conversion and orchestration."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from md2tex.errors_warnings import InputException, Warnings
from md2tex.parser import parse
from md2tex.renderer import RenderOptions, render_tex


def convert_markdown_to_tex(
    inpath: str,
    outpath: str | None = None,
    tex: bool = False,
    template: str | None = None,
    french_quote: bool = False,
    unnumbered: bool = False,
    document_class: str = "article",
    code_backend: str = "auto",
    shell_escape: bool = False,
) -> tuple[str, str]:
    """Convert a Markdown file to a TeX file.
    
    Returns a tuple of (data, outpath).
    """
    if template is None:
        import importlib.resources
        template = str(importlib.resources.files("md2tex").joinpath("data/template.tex"))

    if not re.search(r"\.md$", inpath):
        raise InputException("not_md", inpath)
    if not os.path.isfile(inpath):
        raise InputException("not_inpath", inpath)
    if outpath is None:
        outpath = "output/" + re.sub(r'\..+?$', '.tex', Path(inpath).name)
    elif "/" in outpath and "\\" in outpath:
        raise InputException("outpath_slashes", outpath)
    elif os.path.isdir(outpath):
        outpath = f"{outpath}/{Path(inpath).name}"
    if not re.search(r"\.tex$", outpath):
        Warnings("outpath_extension", outpath)
        outpath = re.sub(r"$", ".tex", outpath)
    if not re.search("^(book|article)$", document_class):
        raise InputException("document_class", document_class)
    if code_backend not in {"auto", "minted", "listings"}:
        raise ValueError(f"Unsupported code backend `{code_backend}`")

    # build output directory
    outdir = os.path.dirname(outpath)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir)
    elif not outdir and not os.path.exists("./output"):
        os.makedirs("./output")

    # open file and read contents
    with open(inpath) as fh:
        data = fh.read()

    # ==================== CONVERT THE FILE ==================== #
    options = RenderOptions(
        document_class=document_class,
        unnumbered=unnumbered,
        french_quote=french_quote,
        code_backend=_resolve_code_backend(code_backend, shell_escape),
    )
    document = parse(data)

    from md2tex.nodes import Heading
    title_data = ""
    # Extract the first Heading(level=1) if present
    if document and isinstance(document[0], Heading) and document[0].level == 1:
        title_node: Heading = document.pop(0)  # type: ignore[assignment]
        from md2tex.escaping import escape_tex
        from md2tex.renderer import _apply_inline_formatting
        
        safe_title = escape_tex(title_node.text)
        safe_title = _apply_inline_formatting(safe_title, options)
        
        title_data = (
            "\\begin{titlepage}\n"
            "    \\vspace*{5cm}\n"
            "    \\begin{center}\n"
            f"        \\Huge \\textbf{{{safe_title}}}\n"
            "    \\end{center}\n"
            "    \\vfill\n"
            "\\end{titlepage}\n"
        )

    body_tex = render_tex(document, options)

    # ==================== BUILD + WRITE OUTPUT TO FILE ==================== #
    if tex is True:
        try:
            with open(template) as fh:
                tex_template = fh.read()
                if "@@BODYTOKEN@@" not in tex_template:
                    raise InputException("template_no_token", template)
                else:
                    backend = _resolve_code_backend(code_backend, shell_escape)
                    tex_template = tex_template.replace("@@DOCUMENTCLASSTOKEN@@", document_class)
                    tex_template = tex_template.replace(
                        "@@CODEPACKAGES@@",
                        _code_packages_block(backend),
                    )
                    tex_template = tex_template.replace("@@TITLETOKEN@@", title_data)
                    data = tex_template.replace("@@BODYTOKEN@@", body_tex)
        except FileNotFoundError:
            raise InputException("not_template", template)
    else:
        data = body_tex
    try:
        with open(outpath, mode="w") as fh:
            fh.write(data)
    except FileNotFoundError:
        raise InputException("not_outpath", outpath)

    return data, outpath


def _resolve_code_backend(code_backend: str, shell_escape: bool) -> str:
    if code_backend == "auto":
        return "minted" if shell_escape else "listings"
    return code_backend


def _code_packages_block(code_backend: str) -> str:
    if code_backend == "minted":
        return (
            "\\usepackage{xcolor}\n"
            "\\usepackage{listings}\n"
            "\\lstset{%\n"
            "\tbasicstyle=\\footnotesize\\ttfamily\\linespread{1}\\selectfont,%\n"
            "\tnumbers=left,%\n"
            "\tbackgroundcolor=\\color{lightgray},%\n"
            "\tshowstringspaces=false,%\n"
            "\tbreaklines=true%\n"
            "}\n"
            "\\usepackage[newfloat]{minted}\n"
            "\\SetupFloatingEnvironment{listing}{}\n"
            "\\usemintedstyle{emacs}\n"
            "\\setminted{linenos, breaklines, tabsize=4, bgcolor=lightgray}"
        )

    return (
        "\\usepackage{xcolor}\n"
        "\\usepackage{listings}\n"
        "\\lstset{%\n"
        "\tbasicstyle=\\footnotesize\\ttfamily\\linespread{1}\\selectfont,%\n"
        "\tnumbers=left,%\n"
        "\tbackgroundcolor=\\color{lightgray},%\n"
        "\tshowstringspaces=false,%\n"
        "\tbreaklines=true%\n"
        "}"
    )


def compile_tex_to_pdf(
    tex_path: str,
    shell_escape: bool = False,
    runs: int = 2,
    cleanup: bool = True,
) -> tuple[bool, str, str | None]:
    if not os.path.isfile(tex_path):
        return False, f"TeX file not found: {tex_path}", None

    if shutil.which("pdflatex") is None:
        return False, "pdflatex is not installed or not in PATH.", None

    tex_file = Path(tex_path)
    cwd = tex_file.parent if tex_file.parent else Path(".")
    command = ["pdflatex", "-interaction=nonstopmode"]
    if shell_escape:
        command.append("-shell-escape")
    command.append(tex_file.name)

    logs: list[str] = []
    for _ in range(max(runs, 1)):
        process = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        logs.append(process.stdout or "")
        logs.append(process.stderr or "")
        if process.returncode != 0:
            summary = _summarize_latex_error("\n".join(logs))
            return False, summary, None

    pdf_path = str(tex_file.with_suffix(".pdf"))
    if os.path.isfile(pdf_path):
        if cleanup:
            _cleanup_latex_artifacts(tex_file)
        return True, "PDF compilation completed successfully.", pdf_path

    return False, "Compilation finished but no PDF file was generated.", None


def _summarize_latex_error(log_text: str) -> str:
    if "Package minted Error: You must invoke LaTeX with the -shell-escape flag." in log_text:
        return (
            "LaTeX failed because minted requires -shell-escape. "
            "Enable shell-escape or use listings backend."
        )

    error_lines = [line.strip() for line in log_text.splitlines() if line.strip().startswith("!")]
    if error_lines:
        return f"LaTeX compilation failed: {error_lines[0]}"
    return "LaTeX compilation failed. Check pdflatex output for details."


def _cleanup_latex_artifacts(tex_file: Path) -> None:
    artifacts = [
        tex_file.with_suffix(".aux"),
        tex_file.with_suffix(".log"),
        tex_file.with_suffix(".out"),
        tex_file.with_suffix(".toc"),
        tex_file.with_suffix(".synctex.gz"),
    ]
    for artifact in artifacts:
        if artifact.exists():
            artifact.unlink()

    minted_dir = tex_file.parent / f"_minted-{tex_file.stem}"
    if minted_dir.exists() and minted_dir.is_dir():
        shutil.rmtree(minted_dir)
