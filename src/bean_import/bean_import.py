import typer
from pathlib import Path
from rich.console import Console
from rich.theme import Theme
from typing_extensions import Annotated

def bean_import(
    ofx: Annotated[Path, typer.Argument(help="The ofx file to parse", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    ledger: Annotated[Path, typer.Argument(help="The beancount ledger file to base the parser from", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    output: Annotated[Path, typer.Option(help="The output file to write to instead of stdout", show_default=False, exists=False)]=None
):
    """
    Parse an OFX file based on a beancount LEDGER and output transaction entries to stdout

    Optionally specify an --output file
    """

    theme = Theme({
        "file": "grey50",
        "error": "red"
    })

    console = Console(theme=theme)
    console_output = f"Parsing: [file]{ofx}[/] with [file]{ledger}[/]"
    
    if output: console_output +=  f"and outputting to [file]{output}[/]"
    console.print(f"{console_output}")
