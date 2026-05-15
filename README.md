# `md2tex` - Markdown to LaTeX Converter

## md2tex
`md2tex` is a powerful, customizable open-source converter that safely translates your standard and GitHub Flavored Markdown (GFM) logic into pure TeX syntax. 

Originally built as a simple parser, `md2tex` has been **completely modernized** into a robust parsing pipeline powered by an Intermediate Representation (IR) AST structure that guarantees 100% stable parsing without colliding formatting conflicts.

---

## Features
- **Strict AST Architecture**: Guaranteed reliable markdown block parsing before inline TeX escaping prevents artifacts.
- **TUI Dashboard**: Native Textual Terminal User Interface for configuration-free execution.
- **Full Template Control**: Automatically wrap logic in predefined headers, or inject converted contents seamlessly into custom TeX template `@@BODYTOKEN@@` blocks.
- **GFM Support**: Full implicit translation of `Tables`, `Strikethroughs`, Code Blocks, Headers, References from standard Markdowns directly into `tabular`, `sout`, `minted`, `section`, etc.
- **Quotes**: Native parameter translation into French inline formatting `\enquote{}` via `csquotes`.

---

## Installation

It is highly recommended to manage implementations via modern package tooling [uv](https://docs.astral.sh/uv/#highlights).

### 1. Simple installation
```bash
git clone git@github.com:Malk97sc/md2tex.git
cd md2tex

# We strongly recommend using the interactive TUI
pip install ".[tui]"
```

### 2. Developing
```bash
git clone git@github.com:Malk97sc/md2tex.git
cd md2tex

# Setup tests and developer linting suites
uv sync
```

### 3. LaTeX Requirements
For local PDF compilation of your `.tex` files, you need `pdflatex` installed. On Unix systems, you can install TeX Live:

#### Ubuntu / Debian / Mint:
```bash
sudo apt update
sudo apt install texlive-latex-extra texlive-fonts-recommended
```

#### Fedora / RHEL:
```bash
sudo dnf install texlive-scheme-medium
```

#### macOS (via Homebrew):
```bash
brew install --cask mactex-no-gui
```

---

## Usage

### Place your documents

To use md2tex, we recommend placing your `.md` files inside the [myfiles](/myfiles/) folder.

### Terminal Interface (TUI) Mode - Recommended
Instead of memorizing flags, directly launch a beautiful TUI configuration dashboard:
```bash
md2tex tui

# Or
md2tex interactive
```
The TUI can now convert to `.tex` and optionally compile to `.pdf` with `pdflatex` (2 passes), including an explicit `shell-escape` toggle.

### Direct CLI Conversion
If you're looking for headless automations or quick CLI overrides:

```bash
# General convert (Defaults Article class output to output/<filename>.tex)
md2tex myfiles/document.md
# Or
md2tex path/to/document.md

# Build full encapsulated `.tex` compiling with headers
md2tex path/to/document.md -c

# Advanced custom translation output
md2tex source.md -c -t ./utils/template.tex -o ./export/export.tex -d book -u -f
```

---

## Documentation
For a complete understanding of how this tool abstracts parsing structures, as well as TUI capabilities, please review the documentation directory:
- [System Architecture Overview](docs/architecture.md)
- [Terminal User Interface (TUI)](docs/tui.md)
- [CLI and TUI Parameters (Step by Step)](docs/cli_tui_parameters.md)

---

## License and Authors
Developed by **Paul Kervegan** in August 2022.
Modernized, refactored, and updated with TUI integration by me, *Malak* in 2026.

Released Open Source under GNU GPL v3.
