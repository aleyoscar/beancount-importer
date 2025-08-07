import typer
from .helpers import get_key, set_key, get_json_values, replace_lines, cur, append_lines
from .ledger import ledger_load, ledger_bean
from .ofx import ofx_load, ofx_pending, ofx_matches
from .prompts import resolve_toolbar, cancel_bindings, cancel_toolbar, confirm_toolbar, ValidOptions, valid_float, valid_account
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
# from prompt_toolkit.formatted_text import HTML
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

def get_posting(type, default_amount, default_currency, completer):
    account = prompt(
        f"...{type} account > ",
        validator=valid_account,
        completer=completer)
    amount = prompt(
        f"...{type} amount > ",
        validator=valid_float,
        default=cur(default_amount))
    currency = prompt(
        f"...{type} currency > ",
        default=default_currency)
    return {"account": account, "amount": amount, "currency": currency}

def bean_import(
    ofx: Annotated[Path, typer.Argument(help="The ofx file to parse", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    ledger: Annotated[Path, typer.Argument(help="The beancount ledger file to base the parser from", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    output: Annotated[Path, typer.Option(help="The output file to write to instead of stdout", show_default=False, exists=False)]=None,
    period: Annotated[str, typer.Option(help="Specify a year, month or day period to parse from the ofx file in the format YYYY, YYYY-MM or YYYY-MM-DD", callback=period_callback)]="",
    payees: Annotated[Path, typer.Option(help="The payee file to use for name substitutions", exists=False)]="payees.json"
):
    """
    Parse an OFX file based on a beancount LEDGER and output transaction entries to stdout

    Optionally specify an --output file
    Optionally specify a time --period in the format YYYY, YYYY-MM or YYYY-MM-DD
    Optionally specify a --payees json file to use for payee name substitutions
    """

    theme = Theme({
        "number": "blue",
        "date": "orange4",
        "flag": "magenta",
        "error": "red",
        "file": "grey50",
        "string": "green",
        "warning": "yellow",
        "answer": "cyan"
    })

    console = Console(theme=theme)
    err_console = Console(theme=theme, stderr=True)
    console_output = f"OFX File: [file]{ofx}[/]\nLEDGER File: [file]{ledger}[/]\nPAYEES File: [file]{payees}[/]"
    buffer = ''

    if output: console_output +=  f"\nOUTPUT File: [file]{output}[/]"
    console.print(f"{console_output}")

    # Parse ofx file into ofx_data
    ofx_data = ofx_load(err_console, ofx)
    if ofx_data and len(ofx_data.transactions):
        console.print(f"Parsed [number]{len(ofx_data.transactions)}[/] transactions from OFX file")
    else:
        err_console.print(f"[warning]No transactions found in OFX file. Exiting.[/]")
        raise typer.Exit()

    # Parse ledger file into ledger_data
    ledger_data = ledger_load(err_console, ledger)
    if ledger_data and len(ledger_data.transactions):
        console.print(f"Parsed [number]{len(ledger_data.transactions)}[/] beans from LEDGER file")
        console.print(f"Default currency: [answer]{ledger_data.currency}[/]")
    else:
        err_console.print(f"[warning]No transaction entries found in LEDGER file. Exiting.[/]")
        raise typer.Exit()
    account_completer = FuzzyCompleter(WordCompleter(ledger_data.accounts, sentence=True))

    # Filter transactions by dates specified from cli
    if period:
        filtered = [t for t in ofx_data.transactions if t.date.startswith(period)]
        if len(filtered):
            console.print(f"Found [number]{len(filtered)}[/] transactions within period [date]{period}[/]")
        else:
            err_console.print(f"[warning]No transactions found within the specified period [date]{period}[/]. Exiting.[/]")
            raise typer.Exit()
    else:
        filtered = ofx_data.transactions

    # Match transactions not in beans into pending
    pending = ofx_pending(filtered, ledger_data.transactions, ofx_data.account_id)
    if len(pending):
        console.print(f"Found [number]{len(pending)}[/] transactions not in LEDGER")
    else:
        err_console.print(f"[warning]No pending transactions found. Exiting.[/]")

    # Parse each pending transaction
    for txn in pending:
        console.print(f"Parsing: {txn.print(theme=True)}")

        # Reconcile, Insert, Skip?
        resolve = prompt(
            f"...Reconcile, Insert or Skip? > ",
            bottom_toolbar=resolve_toolbar,
            validator=ValidOptions(['r', 'reconcile', 'i', 'insert', 's', 'skip', 'q', 'quit'])).lower()

        # Replace payee
        if resolve[0] == 'r' or resolve[0] == 'i':
            payee_completer = FuzzyCompleter(WordCompleter(get_json_values(payees), sentence=True))
            payee = get_key(payees, txn.payee)

            # Payee not found, replace
            if not payee:
                payee = prompt(
                    f"...Replace '{txn.payee}'? > ",
                    key_bindings=cancel_bindings,
                    bottom_toolbar=cancel_toolbar,
                    completer=payee_completer)

            # Payee entered
            if payee:
                console.print(f"...Replaced [string]{txn.payee}[/] with [answer]{payee}[/]")
                set_key(payees, txn.payee, payee)
                txn.payee = payee

        # Reconcile
        if resolve[0] == "r":
            console.print(f"...Reconciling")
            reconcile_matches = ofx_matches(txn, ledger_data.transactions)

            # Matches found
            if len(reconcile_matches):
                console.print(f"...Found matches:\n")
                for i, match in enumerate(reconcile_matches):
                    console.print(f"   [{i}] {match.print_head(theme=True)}")
                if len(reconcile_matches) == 1:
                    match_range = '[0]'
                else:
                    match_range = f'[0-{len(reconcile_matches) - 1}]'
                reconcile_match = prompt(
                    f"\n...Select match {match_range} > ",
                    bottom_toolbar=cancel_toolbar,
                    key_bindings=cancel_bindings,
                    validator=ValidOptions([str(n) for n in range(len(reconcile_matches))]),
                    default="0")
                if reconcile_match:
                    bean_reconcile = reconcile_matches[int(reconcile_match)]
                    bean_linecount = len(bean_reconcile.print().strip().split('\n'))
                    console.print(f"...Reconciling {bean_reconcile.print_head(theme=True)}\n")
                    bean_reconcile.entry.meta.update({'account': ofx_data.account_id, 'id': txn.id})
                    replace_lines(
                        err_console,
                        bean_reconcile.entry.meta['filename'],
                        bean_reconcile.print().strip(),
                        bean_reconcile.entry.meta['lineno'],
                        bean_linecount)
                    console.print(bean_reconcile.print())

            # No matches found
            else:
                reconcile_insert = prompt(
                    f"...No matching transactions found. Would you like to insert instead? [Y/n] > ",
                    default='y',
                    bottom_toolbar=confirm_toolbar,
                    validator=ValidOptions(['y', 'n'])).lower()
                if reconcile_insert == 'y': resolve = 'i'
                else: resolve = 's'

        # Insert
        if resolve[0] == "i":
            console.print(f"...Inserting")

            # Add credit postings until total is equal to transaction amount
            new_bean = ledger_bean(txn, ofx_data.account_id)
            while new_bean.amount < txn.amount:
                console.print(f"\n{new_bean.print()}")
                new_bean.add_posting(get_posting("Credit", txn.amount - new_bean.amount, ledger_data.currency, account_completer))

            # Add debit posting
            console.print(f"\n{new_bean.print()}")
            new_bean.add_posting(get_posting("Debit", txn.amount * -1, ledger_data.currency, account_completer))

            # Display final and prompt for edits
            console.print(f"\n{new_bean.print()}")

            # Edit final

            # Post entry to output (if stdout, save to string)
            if output:
                console_insert = f'[file]{output}[/]'
                append_lines(err_console, output, new_bean.print())
            else:
                console_insert = f'[file]buffer[/]'
                buffer += new_bean.print()
            console.print(f"...Inserted {new_bean.print_head(theme=True)} into {console_insert}")
        # Skip transaction
        if resolve[0] == "s":
            console.print(f"...Skipping")

        # Quit
        if resolve[0] == "q":
            break

    # Finished parsing
    console.print(f"[string]Finished parsing [number]{len(pending)}[/] transactions[/]\n")
    if not output and buffer:
        console.print(buffer)
    console.print(f"[warning]Exiting[/]")
