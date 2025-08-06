import typer
from typing_extensions import Annotated
from rich.console import Console
from rich.theme import Theme
theme = Theme({
    "file": "grey50",
    "error": "red"
})

def bean_import(
    ofx: Annotated[str, typer.Argument(help="The ofx file to parse")],
    ledger: Annotated[str, typer.Argument(help="The beancount ledger file to base the parser from")],
    output: Annotated[str, typer.Option(help="The output file to write to instead of stdout", show_default=False)]="stdout"
):
    """
    Parse an OFX file based on a beancount LEDGER and output transaction entries to stdout

    Optionally specify an --output file
    """
    console = Console(theme=theme)
    console.print(f"Parsing: [file]{ofx}[/] with [file]{ledger}[/] and outputting to [file]{output}[/]")
