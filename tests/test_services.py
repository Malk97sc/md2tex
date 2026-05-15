"""Service-level tests for conversion and LaTeX compilation."""

from __future__ import annotations

from pathlib import Path

from md2tex.services import compile_tex_to_pdf, convert_markdown_to_tex


def test_convert_complete_tex_with_minted_backend(tmp_path: Path) -> None:
    md_file = tmp_path / "code.md"
    out_file = tmp_path / "code.tex"
    md_file.write_text("```python\nprint('hi')\n```\n")

    content, outpath = convert_markdown_to_tex(
        inpath=str(md_file),
        outpath=str(out_file),
        tex=True,
        code_backend="minted",
        shell_escape=True,
    )

    assert outpath == str(out_file)
    assert "\\usepackage{xcolor}" in content
    assert "\\linespread{1}\\selectfont" in content
    assert "\\usepackage[newfloat]{minted}" in content
    assert "\\begin{minted}{python}" in content


def test_convert_complete_tex_with_listings_backend(tmp_path: Path) -> None:
    md_file = tmp_path / "code.md"
    out_file = tmp_path / "code.tex"
    md_file.write_text("```python\nprint('hi')\n```\n")

    content, _ = convert_markdown_to_tex(
        inpath=str(md_file),
        outpath=str(out_file),
        tex=True,
        code_backend="listings",
        shell_escape=False,
    )

    assert "\\usepackage{xcolor}" in content
    assert "\\linespread{1}\\selectfont" in content
    assert "\\usepackage[newfloat]{minted}" not in content
    assert "\\begin{minted}{python}" not in content
    assert "\\begin{lstlisting}" in content


def test_convert_complete_tex_auto_without_shell_escape_uses_listings(tmp_path: Path) -> None:
    md_file = tmp_path / "code.md"
    out_file = tmp_path / "code.tex"
    md_file.write_text("```python\nprint('hi')\n```\n")

    content, _ = convert_markdown_to_tex(
        inpath=str(md_file),
        outpath=str(out_file),
        tex=True,
        code_backend="auto",
        shell_escape=False,
    )

    assert "\\usepackage[newfloat]{minted}" not in content
    assert "\\begin{lstlisting}" in content


def test_body_tokens_are_not_replaced_inside_markdown_content(tmp_path: Path) -> None:
    md_file = tmp_path / "tokens.md"
    out_file = tmp_path / "tokens.tex"
    md_file.write_text(
        "- `@@BODYTOKEN@@`\n"
        "- `@@TITLETOKEN@@`\n"
        "- `@@DOCUMENTCLASSTOKEN@@`\n"
        "- `@@CODEPACKAGES@@`\n"
    )

    content, _ = convert_markdown_to_tex(
        inpath=str(md_file),
        outpath=str(out_file),
        tex=True,
        code_backend="auto",
        shell_escape=False,
    )

    assert "\\texttt{@@BODYTOKEN@@}" in content
    assert "\\texttt{@@TITLETOKEN@@}" in content
    assert "\\texttt{@@DOCUMENTCLASSTOKEN@@}" in content
    assert "\\texttt{@@CODEPACKAGES@@}" in content


def test_compile_tex_to_pdf_reports_missing_pdflatex(tmp_path: Path, monkeypatch) -> None:
    tex_file = tmp_path / "doc.tex"
    tex_file.write_text("\\documentclass{article}\\begin{document}Hi\\end{document}")

    monkeypatch.setattr("md2tex.services.shutil.which", lambda _: None)

    ok, message, pdf_path = compile_tex_to_pdf(str(tex_file))
    assert not ok
    assert "pdflatex is not installed" in message
    assert pdf_path is None


def test_compile_tex_to_pdf_reports_minted_shell_escape_error(tmp_path: Path, monkeypatch) -> None:
    tex_file = tmp_path / "doc.tex"
    tex_file.write_text("\\documentclass{article}\\begin{document}Hi\\end{document}")

    monkeypatch.setattr("md2tex.services.shutil.which", lambda _: "/usr/bin/pdflatex")

    class Result:
        returncode = 1
        stdout = ""
        stderr = "Package minted Error: You must invoke LaTeX with the -shell-escape flag."

    monkeypatch.setattr("md2tex.services.subprocess.run", lambda *args, **kwargs: Result())

    ok, message, pdf_path = compile_tex_to_pdf(str(tex_file), shell_escape=False)
    assert not ok
    assert "minted requires -shell-escape" in message
    assert pdf_path is None


def test_compile_tex_to_pdf_cleans_artifacts_on_success(tmp_path: Path, monkeypatch) -> None:
    tex_file = tmp_path / "tui.tex"
    pdf_file = tmp_path / "tui.pdf"
    tex_file.write_text("\\documentclass{article}\\begin{document}Hi\\end{document}")
    pdf_file.write_text("pdf")

    for suffix in (".aux", ".log", ".out", ".toc", ".synctex.gz"):
        (tmp_path / f"tui{suffix}").write_text("residual")

    minted_dir = tmp_path / "_minted-tui"
    minted_dir.mkdir()
    (minted_dir / "dummy.pyg").write_text("x")

    monkeypatch.setattr("md2tex.services.shutil.which", lambda _: "/usr/bin/pdflatex")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("md2tex.services.subprocess.run", lambda *args, **kwargs: Result())

    ok, message, out_pdf = compile_tex_to_pdf(str(tex_file), cleanup=True)
    assert ok
    assert "completed successfully" in message
    assert out_pdf == str(pdf_file)

    for suffix in (".aux", ".log", ".out", ".toc", ".synctex.gz"):
        assert not (tmp_path / f"tui{suffix}").exists()
    assert not minted_dir.exists()
