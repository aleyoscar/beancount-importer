import typer
from .ofx import ofx_load
from pathlib import Path
from prompt_toolkit import PromptSession
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
        "number": "blue",
        "date": "yellow",
        "error": "red",
        "file": "grey50",
        "string": "green"
    })

    console = Console(theme=theme)
    err_console = Console(theme=theme, stderr=True)
    console_output = f"Parsing: [file]{ofx}[/] with [file]{ledger}[/]"

    session = PromptSession()

    if output: console_output +=  f"and outputting to [file]{output}[/]"
    console.print(f"{console_output}")

    # Parse ofx file into transactions
    ofx_data = ofx_load(err_console, ofx)
    console.print(f"Parsed [number]{len(ofx_data['transactions'])}[/] transactions from OFX file")
    
    # Parse ledger file into beans
    # Filter transactions by dates specified from cli
    # Match transactions not in beans into pending
    # Parse each pending transaction
        # Check if payee in payee file
            # YES: replace
            # NO: Prompt for replacement and update payee file
        # Loop inserting postings
            # Add until postings total is equal to transaction amount
            # Add a final posting
        # Display final and prompt for edits
            # Edit selected
        # Post entry to output (if stdout, save to string)
