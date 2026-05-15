# CLI and TUI Parameters (Step by Step)

## About

This guide explains the command:

```bash
md2tex source.md -c -t ./utils/template.tex -o ./export/export.tex -d book -u -f
```

and how to set the same options in the TUI.

## 1. Base input

```bash
md2tex source.md
```

- `source.md` is the required input Markdown file.
- It must exist and use `.md` extension.

TUI equivalent:
- `Input Markdown File (*.md) [required]` = `source.md`

## 2. Build a complete TeX document

```bash
-c
```

- Enables complete TeX output (preamble + `\\begin{document}` + `\\end{document}` + TOC support).
- Without `-c`, output is body-only TeX content.

TUI equivalent:
- Enable `Complete TeX file (-c)`

## 3. Use a custom TeX template

```bash
-t ./utils/template.tex
```

- Uses a custom template instead of the bundled default template.
- The template must include `@@BODYTOKEN@@`.
- Common pattern: keep preamble/style in template and inject converted Markdown body at `@@BODYTOKEN@@`.

TUI equivalent:
- `Template File (*.tex) [optional]` = `./utils/template.tex`

### What is a template in md2tex?

A template is a complete `.tex` skeleton that `md2tex` uses as a wrapper around converted Markdown content.

Think of it as:
- Your LaTeX layout/style (preamble, fonts, margins, packages)
- Plus one placeholder where converted Markdown will be inserted

Required token:
- `@@BODYTOKEN@@` (mandatory): replaced with converted body content

Optional tokens supported by md2tex default flow:
- `@@DOCUMENTCLASSTOKEN@@`: replaced with `article` or `book`
- `@@TITLETOKEN@@`: replaced with the generated title page (if first Markdown heading is level 1)
- `@@CODEPACKAGES@@`: replaced with code package setup (`listings`/`minted` + `xcolor`) according to backend strategy

Minimal valid custom template example:

```tex
\\documentclass{@@DOCUMENTCLASSTOKEN@@}
@@CODEPACKAGES@@
\\begin{document}
@@TITLETOKEN@@
@@BODYTOKEN@@
\\end{document}
```

If `@@BODYTOKEN@@` is missing, conversion fails because md2tex has nowhere to inject the Markdown output.

## 4. Choose custom output path

```bash
-o ./export/export.tex
```

- Writes output to `./export/export.tex`.
- If directory does not exist, it is created.
- If extension is missing, `.tex` is appended.

TUI equivalent:
- `Output TeX File (*.tex) [optional]` = `./export/export.tex`

## 5. Select document class

```bash
-d book
```

- Sets TeX document class to `book`.
- Allowed values: `article` or `book`.
- Affects heading mapping (`#` as `\\chapter{}` in `book`, `\\section{}` in `article`).

TUI equivalent:
- `document_class` selector = `book`

## 6. Convert headings as unnumbered

```bash
-u
```

- Uses unnumbered section commands (e.g., `\\chapter*{}`, `\\section*{}`).
- The converter still adds TOC entries with `\\addcontentsline`.

TUI equivalent:
- Enable `Unnumbered headers (-u)`

## 7. Convert inline quotes to French quotes

```bash
-f
```

- Converts inline quoted text to `\\enquote{...}` (via `csquotes`).

TUI equivalent:
- Enable `French quotes (-f)`

## Full mapping summary

- CLI `source.md` -> TUI `Input Markdown File`
- CLI `-c` -> TUI `Complete TeX file (-c)`
- CLI `-t PATH` -> TUI `Template File`
- CLI `-o PATH` -> TUI `Output TeX File`
- CLI `-d book|article` -> TUI `document_class`
- CLI `-u` -> TUI `Unnumbered headers (-u)`
- CLI `-f` -> TUI `French quotes (-f)`

## Extra options you can also use

CLI:

```bash
--code-backend auto|minted|listings
--shell-escape
```

TUI equivalents:
- `Enable shell-escape` toggle
- Code backend is `auto` by default:
  - shell-escape enabled -> `minted`
  - shell-escape disabled -> `listings`

## Practical examples

1. Minimal conversion:

```bash
md2tex myfiles/example.md
```

2. Complete book with custom template and output:

```bash
md2tex myfiles/example.md -c -t ./templates/book.tex -o ./build/notes.tex -d book -u -f
```

3. Force minted with shell-escape expectations:

```bash
md2tex myfiles/example.md -c --code-backend minted --shell-escape
```
