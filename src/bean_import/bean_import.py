import typer
from .ofx import ofx_load, ofx_pending
from .ledger import ledger_load
from pathlib import Path
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.theme import Theme
from typing_extensions import Annotated

def period_callback(date_str: str):
    if not date_str: return date_str
    error = "Please enter a valid date format for --period (YYYY, YYYY-MM or YYYY-MM-DD)"
    if not all(c.isdigit() or c == '-' for c in date_str): raise typer.BadParameter(error)

    parts = date_str.split('-')
    num_parts = len(parts)

    if num_parts not in (1, 2, 3): raise typer.BadParameter(error)
    if not (parts[0].isdigit() and len(parts[0]) == 4): raise typer.BadParameter(error)
    if num_parts == 1: return date_str
    if not (parts[1].isdigit() and len(parts[1]) == 2 and 1 <= int(parts[1]) <= 12): raise typer.BadParameter(error)
    if num_parts == 2: return date_str
    if not (parts[2].isdigit() and len(parts[2]) == 2 and 1 <= int(parts[2]) <= 31): raise typer.BadParameter(error)

    return date_str

def bean_import(
    ofx: Annotated[Path, typer.Argument(help="The ofx file to parse", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    ledger: Annotated[Path, typer.Argument(help="The beancount ledger file to base the parser from", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    output: Annotated[Path, typer.Option(help="The output file to write to instead of stdout", show_default=False, exists=False)]=None,
    period: Annotated[str, typer.Option(help="Specify a year, month or day period to parse from the ofx file in the format YYYY, YYYY-MM or YYYY-MM-DD", callback=period_callback)]=""
):
    """
    Parse an OFX file based on a beancount LEDGER and output transaction entries to stdout

    Optionally specify an --output file
    Optionally specify a time --period in the format YYYY, YYYY-MM or YYYY-MM-DD
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

    # Parse ofx file into ofx_data
    ofx_data = ofx_load(err_console, ofx)
    console.print(f"Parsed [number]{len(ofx_data['transactions'])}[/] transactions from OFX file")

    # Parse ledger file into ledger_data
    ledger_data = ledger_load(err_console, ledger)
    console.print(f"Parsed [number]{len(ledger_data['transactions'])}[/] beans from LEDGER file")

    # Filter transactions by dates specified from cli
    if period:
        filtered = [t for t in ofx_data['transactions'] if t.date.startswith(period)]
        console.print(f"Found [number]{len(filtered)}[/] transactions within period [number]{period}[/]")
    else:
        filtered = ofx_data['transactions']
    
    # Match transactions not in beans into pending
    pending = ofx_pending(filtered, ledger_data['transactions'], ofx_data['account_info']['account_id'])
    if len(pending):
        console.print(f"Found [number]{len(pending)}[/] transactions not in LEDGER")
    else:
        err_console.print(f"[warning]No pending transactions found. Exiting.[/]")

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
