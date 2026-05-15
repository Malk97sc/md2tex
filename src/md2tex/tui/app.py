"""Textual application for md2tex."""

from __future__ import annotations

import os
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, Select, Checkbox, Button, RichLog

from md2tex.services import compile_tex_to_pdf, convert_markdown_to_tex


class Md2TexApp(App):
    """Textual TUI for md2tex."""

    TITLE = "md2tex TUI"

    CSS = """
    Screen {
        layout: vertical;
    }
    #form-container {
        padding: 1 2;
        height: auto;
    }
    .row {
        height: auto;
        margin-bottom: 1;
    }
    .row Checkbox {
        margin-right: 2;
    }
    .row Select {
        width: 30;
    }
    #logs {
        border-top: solid green;
        height: 1fr;
        padding: 1;
    }
    Input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the layout of the app."""
        yield Header()
        with Container(id="form-container"):
            yield Input(placeholder="Input Markdown File (*.md) [required]", id="inpath")
            yield Input(placeholder="Output TeX File (*.tex) [optional]", id="outpath")
            yield Input(placeholder="Template File (*.tex) [optional]", id="template")

            with Horizontal(classes="row"):
                yield Select([("article", "article"), ("book", "book")], id="document_class", value="article")
                yield Checkbox("Complete TeX file (-c)", id="tex")
                yield Checkbox("Unnumbered headers (-u)", id="unnumbered")
                yield Checkbox("French quotes (-f)", id="french_quote")

            with Horizontal(classes="row"):
                yield Checkbox("Compile PDF", id="compile_pdf")
                yield Checkbox("Enable shell-escape", id="shell_escape")
            with Horizontal(classes="row"):
                yield Button("Convert", id="convert", variant="primary")

        yield RichLog(id="logs", highlight=True, markup=True)
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "convert":
            self.run_conversion()

    def run_conversion(self) -> None:
        """Run the conversion safely without crashing the TUI."""
        log = self.query_one("#logs", RichLog)
        inpath = self.query_one("#inpath", Input).value.strip()
        outpath = self.query_one("#outpath", Input).value.strip() or None
        template = self.query_one("#template", Input).value.strip() or None
        document_class = str(self.query_one("#document_class", Select).value or "article")
        
        # Checkbox widgets may not return boolean cleanly if not configured, but .value is typically bool
        tex = self.query_one("#tex", Checkbox).value
        unnumbered = self.query_one("#unnumbered", Checkbox).value
        french_quote = self.query_one("#french_quote", Checkbox).value
        compile_pdf = self.query_one("#compile_pdf", Checkbox).value
        shell_escape = self.query_one("#shell_escape", Checkbox).value

        log.clear()
        if not inpath:
            log.write("[bold red]Error:[/] Input Markdown File is required.")
            return

        log.write(f"[bold blue]Starting conversion for:[/] {inpath}")

        # Set TUI context variable so that errors don't trigger sys.exit(1)
        os.environ["MD2TEX_TUI"] = "1"
        try:
            data, final_outpath = convert_markdown_to_tex(
                inpath=inpath,
                outpath=outpath,
                tex=tex,
                template=template,
                french_quote=french_quote,
                unnumbered=unnumbered,
                document_class=document_class,
                code_backend="auto",
                shell_escape=shell_escape,
            )
            log.write(f"[bold green]Success:[/] TeX file created at [bold]{final_outpath}[/]")
            log.write(f"[gray]Output size: {len(data)} characters[/]")

            if compile_pdf:
                log.write("[bold blue]Compiling PDF with pdflatex (2 passes)...[/]")
                ok, message, pdf_path = compile_tex_to_pdf(
                    tex_path=final_outpath,
                    shell_escape=shell_escape,
                    runs=2,
                )
                if ok:
                    log.write(f"[bold green]Success:[/] PDF created at [bold]{pdf_path}[/]")
                else:
                    log.write(f"[bold red]Compilation error:[/] {message}")
            elif tex:
                log.write(
                    "[yellow]Tip:[/] This document may require compilation with "
                    "`pdflatex -shell-escape` when using minted code blocks."
                )
        except Exception as e:
            # We intercept base exceptions (which will be InputException mostly)
            # e.message is safely caught string
            err_msg = getattr(e, "message", str(e))
            log.write(f"[bold red]Error:[/] {err_msg}")
        finally:
            os.environ.pop("MD2TEX_TUI", None)

def run_tui() -> None:
    """Launch the textual UI."""
    app = Md2TexApp()
    app.run()
