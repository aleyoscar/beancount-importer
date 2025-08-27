import typer
from .helpers import get_key, set_key, get_json_values, replace_lines, cur, append_lines
from .ledger import ledger_load, ledger_bean
from .ofx import ofx_load, ofx_pending, ofx_matches
from .prompts import resolve_toolbar, cancel_bindings, cancel_toolbar, confirm_toolbar, ValidOptions, valid_float, valid_account, edit_toolbar, valid_date, valid_link_tag, is_account
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
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

def account_callback(acct_str: str):
    if not acct_str: return acct_str
    if not is_account(acct_str): raise typer.BadParameter("Please enter a valid beancount account, EX: 'Assets:Savings'")
    return acct_str

def get_posting(type, default_amount, default_currency, op_cur, completer):
    account = prompt(
        f"...{type} account > ",
        validator=valid_account,
        completer=completer)
    amount = prompt(
        f"...{type} amount > ",
        validator=valid_float,
        default=cur(default_amount))
    if not op_cur:
        currency = prompt(
            f"...{type} currency > ",
            default=default_currency)
    else:
        currency = default_currency
    return {"account": account, "amount": amount, "currency": currency}

def bean_import(
    ofx: Annotated[Path, typer.Argument(help="The ofx file to parse", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    ledger: Annotated[Path, typer.Argument(help="The beancount ledger file to base the parser from", exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True)],
    output: Annotated[Path, typer.Option("--output", "-o", help="The output file to write to instead of stdout", show_default=False, exists=False)]=None,
    period: Annotated[str, typer.Option("--period", "-d", help="Specify a year, month or day period to parse from the ofx file in the format YYYY, YYYY-MM or YYYY-MM-DD", callback=period_callback)]="",
    account: Annotated[str, typer.Option("--account", "-a", help="Specify the account the ofx file belongs to", callback=account_callback)]="",
    payees: Annotated[Path, typer.Option("--payees", "-p", help="The payee file to use for name substitutions", exists=False)]="payees.json",
    operating_currency: Annotated[bool, typer.Option("--operating_currency", "-c", help="Skip the currency prompt when inserting and use the ledger's operating_currency", )]=False
):
    """
    Parse an OFX file based on a beancount LEDGER and output transaction entries to stdout

    Optionally specify an --output file.
    Optionally specify a time --period in the format YYYY, YYYY-MM or YYYY-MM-DD.
    Optionally specify a the --account the ofx file belongs to.
    Optionally specify a --payees json file to use for payee name substitutions.
    Optionally skip the currency prompt when inserting and use the ledger's --operating-currency.
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
    tags_completer = FuzzyCompleter(WordCompleter(ledger_data.tags))
    links_completer = FuzzyCompleter(WordCompleter(ledger_data.links))

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

    # Check if account specified, else prompt
    if not account:
        account = prompt(
            f"Beancount account OFX belongs to > ",
            validator=valid_account,
            completer=account_completer)
    console.print(f"OFX file using account: [answer]{account}[/]")

    # Match transactions not in beans into pending
    pending = ofx_pending(filtered, ledger_data.transactions, account)
    if len(pending):
        console.print(f"Found [number]{len(pending)}[/] transactions not in LEDGER")
    else:
        err_console.print(f"[warning]No pending transactions found. Exiting.[/]")

    # Parse each pending transaction
    reconcile_count = 0
    insert_count = 0
    for txn_count, txn in enumerate(pending):
        console.print(f"Parsing {txn_count+1}/{len(pending)}: {txn.print(theme=True)}")

        # Update ledger data for every transaction
        ledger_data = ledger_load(err_console, ledger)
        account_completer = FuzzyCompleter(WordCompleter(ledger_data.accounts, sentence=True))
        tags_completer = FuzzyCompleter(WordCompleter(ledger_data.tags))
        links_completer = FuzzyCompleter(WordCompleter(ledger_data.links))

        # Reconcile, Insert, Skip?
        resolve = prompt(
            f"...Reconcile, Insert or Skip? > ",
            bottom_toolbar=resolve_toolbar,
            validator=ValidOptions(['r', 'reconcile', 'i', 'insert', 's', 'skip', 'q', 'quit'])).lower()

        # Reconcile
        if resolve[0] == "r":
            console.print(f"...Reconciling")
            reconcile_matches = ofx_matches(txn, ledger_data.transactions, account)

            # Matches found
            if len(reconcile_matches):
                console.print(f"...Found matches:\n")
                for i, match in enumerate(reconcile_matches):
                    post_match = None
                    for post in match.entry.postings:
                        if post.account == account:
                            post_match = post
                            break
                    console.print(f"   [{i}] {match.print_head(theme=True)}")
                    console.print(f"          {post_match.account} {post_match.units.number}")
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
                    for post in bean_reconcile.entry.postings:
                        if post.account == account:
                            post.meta.update({'rec': txn.id})
                            break
                    replace_lines(
                        err_console,
                        bean_reconcile.entry.meta['filename'],
                        bean_reconcile.print().strip(),
                        bean_reconcile.entry.meta['lineno'],
                        bean_linecount)
                    console.print(bean_reconcile.print())
                    reconcile_count += 1

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

            # Replace payee
            payees_set = sorted(set(get_json_values(payees)))
            payee_completer = FuzzyCompleter(WordCompleter(payees_set, sentence=True))
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

            # Add credit postings until total is equal to transaction amount
            new_bean = ledger_bean(txn, ofx_data.account_id)
            while new_bean.amount < txn.abs_amount:
                console.print(f"\n{new_bean.print()}")
                new_bean.add_posting(get_posting("Credit", txn.abs_amount - new_bean.amount, ledger_data.currency, operating_currency, account_completer))

            # Add debit posting
            console.print(f"\n{new_bean.print()}")
            new_bean.add_posting(get_posting("Debit", txn.abs_amount * -1, ledger_data.currency, operating_currency, account_completer))

            # Add rec meta to account
            for post in new_bean.entry.postings:
                if post.account == account:
                    post.meta.update({'rec': txn.id})

            # Edit final
            while True:
                console.print(f"\n{new_bean.print()}")
                edit_option = prompt(
                    f"...Edit transaction? > ",
                    validator=ValidOptions(['d', 'date', 'f', 'flag', 'p', 'payee', 'n', 'narration', 't', 'tags', 'l', 'links', 'o', 'postings', 's', 'save']),
                    bottom_toolbar=edit_toolbar)

                # Edit date
                if edit_option[0] == 'd':
                    edit_date = prompt(
                        f"...Enter a new date (YYYY-MM-DD) > ",
                        validator=valid_date,
                        key_bindings=cancel_bindings,
                        bottom_toolbar=cancel_toolbar)
                    if edit_date:
                        new_bean.update(date=edit_date)
                    continue

                # Edit flag
                if edit_option[0] == 'f':
                    edit_flag = prompt(
                        f"...Enter a new flag [!/*] > ",
                        validator=ValidOptions(['*', '!']),
                        key_bindings=cancel_bindings,
                        bottom_toolbar=cancel_toolbar)
                    if edit_flag:
                        new_bean.update(flag=edit_flag)
                    continue

                # Edit payee
                if edit_option[0] == 'p':
                    edit_payee = prompt(
                        f"...Enter new payee > ",
                        key_bindings=cancel_bindings,
                        bottom_toolbar=cancel_toolbar)
                    if edit_payee:
                        new_bean.update(payee=edit_payee)
                    continue

                # Edit narration
                if edit_option[0] == 'n':
                    edit_narration = prompt(
                        f"...Enter new narration > ",
                        key_bindings=cancel_bindings,
                        bottom_toolbar=cancel_toolbar)
                    if edit_narration:
                        new_bean.update(narration=edit_narration)
                    continue

                # Edit tags
                if edit_option[0] == 't':
                    edit_tags = prompt(
                        f"...Enter a list of tags separated by spaces > ",
                        key_bindings=cancel_bindings,
                        bottom_toolbar=cancel_toolbar,
                        validator=valid_link_tag,
                        completer=tags_completer,
                        default=" ".join(new_bean.entry.tags))
                    if edit_tags:
                        new_bean.update(tags=set(edit_tags.split()))
                    continue

                # Edit links
                if edit_option[0] == 'l':
                    edit_links = prompt(
                        f"...Enter a list of links separated by spaces > ",
                        key_bindings=cancel_bindings,
                        bottom_toolbar=cancel_toolbar,
                        validator=valid_link_tag,
                        completer=links_completer,
                        default=" ".join(new_bean.entry.links))
                    if edit_links:
                        new_bean.update(links=set(edit_links.split()))
                    continue

                # Edit postings
                if edit_option[0] == 'o':
                    new_bean.update(postings=[])
                    while new_bean.amount < txn.abs_amount:
                        console.print(f"\n{new_bean.print()}")
                        new_bean.add_posting(get_posting("Credit", txn.abs_amount - new_bean.amount, ledger_data.currency, operating_currency, account_completer))
                    console.print(f"\n{new_bean.print()}")
                    new_bean.add_posting(get_posting("Debit", txn.abs_amount * -1, ledger_data.currency, operating_currency, account_completer))
                    continue

                # Save and finish
                if edit_option[0] == 's':
                    console.print(f"...Finished editing")
                    break

            # Post entry to output (if stdout, save to string)
            if output:
                console_insert = f'[file]{output}[/]'
                append_lines(err_console, output, new_bean.print())
            else:
                console_insert = f'[file]buffer[/]'
                buffer += f"\n{new_bean.print()}"
            console.print(f"...Inserted {new_bean.print_head(theme=True)} into {console_insert}")
            insert_count += 1
        # Skip transaction
        if resolve[0] == "s":
            console.print(f"...Skipping")

        # Quit
        if resolve[0] == "q":
            break

    # Finished parsing
    if not output and buffer:
        console.print(f"{buffer}")
    if reconcile_count:
        console.print(f"[string]Reconciled [number]{reconcile_count}[/] transactions[/]")
    if insert_count:
        console.print(f"[string]Inserted [number]{insert_count}[/] transactions[/]")
    skipped = len(pending) - reconcile_count - insert_count
    if skipped:
        console.print(f"[string]Skipped [number]{skipped}[/] transactions[/]")
    console.print(f"[warning]Finished parsing. Exiting[/]")
