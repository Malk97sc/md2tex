# Architecture

## md2tex

`md2tex` is built around a layered architecture cleanly separating text parsing, abstract representations, escaping mechanisms, and output rendering.

## Core Modules

- **`cli.py` & `tui/`**: User interface layers routing interactions via Click (CLI commands) or Textual (Terminal User Interface). Both interface layers utilize the `md2tex/services.py` core to execute Markdown conversions reliably.
- **`services.py`**: The orchestration layer. It receives requests, standardizes path interactions, constructs `RenderOptions`, calls the parser and renderer, and injects templates.
- **`parser.py`**: A block-level, line-by-line Markdown parser. It scans strings and safely extracts raw block entities (like `CodeBlock`, `BlockQuote`, `Table`, `Heading`) into AST `IR Nodes`. 
- **`nodes.py`**: Simple structure layer outlining the abstract tree (`Table`, `Heading`, `CodeBlock`, `FootnoteDef`, `ListBlock`, etc.).
- **`escaping.py`**: Security translation module correctly escaping character artifacts (`$`, `%`, `{`) *after* blocks are parsed, but *before* formatting runs.
- **`renderer.py`**: Main TeX compilation module processing `IR Nodes`. It handles each node type (e.g., `_render_table`) and recursively processes Inline Formatting via Regex (Italics, Hyperlinks, Strikethrough, etc.).

## Flow of Data
`Markdown String -> Block Parser -> IR Ast (nodes.py) -> Renderer (escape -> format -> inject) -> TeX String`
