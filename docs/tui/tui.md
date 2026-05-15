# Using the TUI

## md2tex

`md2tex` includes a Textual-based TUI so you can convert Markdown to TeX without memorizing CLI flags.

## 1. Install TUI dependency

```bash
pip install ".[tui]"
# or
uv sync --extra tui
```

## 2. Launch the TUI

```bash
md2tex tui
# or
md2tex interactive
```

## 3. Fill the form

- `Input Markdown File (*.md) [required]`: path to your source `.md` file.
- `Output TeX File (*.tex) [optional]`: custom output path. If empty, default output path is used.
- `Template File (*.tex) [optional]`: custom template for complete TeX generation.
- `document_class`: choose `article` or `book`.
- `Complete TeX file (-c)`: wraps output with preamble/template.
- `Unnumbered headers (-u)`: uses unnumbered section commands.
- `French quotes (-f)`: converts inline quotes using `\\enquote{}`.
- `Compile PDF`: runs `pdflatex` twice after conversion.
- `Enable shell-escape`: enables `-shell-escape` in compilation and allows `minted` backend in auto mode.

Press `Convert` to run the selected workflow.

## 4. Understand the result logs

The log panel reports each step explicitly:

- Successful TeX generation: shows exact `.tex` path.
- Successful PDF compilation: shows exact `.pdf` path.
- Temporary LaTeX artifacts are removed automatically (`.aux`, `.log`, `.out`, `.toc`, `.synctex.gz`, `_minted-*`).
- Compilation failure: shows a compact error summary with next action.

## 5. Code block backend behavior

`md2tex` now uses backend strategy `auto` by default:

- With shell-escape enabled: uses `minted` for fenced code blocks with language.
- Without shell-escape: falls back to `listings` to avoid minted compile failures.

This prevents the common error:

`Package minted Error: You must invoke LaTeX with the -shell-escape flag.`

## 6. Step-by-step example

1. Run `md2tex tui`.
2. Set `Input Markdown File` to `docs/tui.md`.
3. Enable `Complete TeX file (-c)`.
4. Enable `Compile PDF`.
5. If you need minted syntax highlighting, enable `Enable shell-escape`.
6. Click `Convert`.
7. Check log lines for generated `.tex` and `.pdf` paths.

## 7. Troubleshooting

- `pdflatex is not installed or not in PATH`:
  install TeX Live/MacTeX and retry.
- `minted requires -shell-escape`:
  enable `Enable shell-escape`, or run without it so backend auto uses `listings`.
- Input path error:
  ensure the input file exists and has `.md` extension.
- Template token error:
  custom template must contain `@@BODYTOKEN@@`.
