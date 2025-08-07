from beancount import loader
from beancount.core.data import Transaction, Posting, Open
from beancount.core.amount import Amount
from beancount.parser import printer
from datetime import datetime
from .helpers import cur
from decimal import Decimal

class Ledger:
    def __init__(self, entries, errors, options):
        self.title = options.get('title', 'Unknown')
        currency = options.get('operating_currency', [])
        self.currency = currency[0] if len(currency) else ''
        self.transactions = [Bean(t) for t in entries if isinstance(t, Transaction)]
        self.accounts = [o.account for o in entries if isinstance(o, Open)]
        self.errors = [str(err) for err in errors] if errors else []

class Bean:
    def __init__(self, entry):
        self.entry = entry
        self.amount = 0.0
        self.total()

    def __str__(self):
        return printer.format_entry(self.entry)

    def print(self):
        return self.__str__()

    def print_head(self, theme=False):
        payee = ''
        narration = ''
        if self.entry.payee:
            payee = f'"{self.entry.payee}"'
            narration = '""'
        if self.entry.narration:
            narration = f'"{self.entry.narration}"'
        tags = self.print_tags()
        links = self.print_links()
        if theme: return f'[date]{self.date}[/] [flag]{self.entry.flag}[/] [string]{payee}[/] [string]{narration}[/] [file]{tags}[/] [file]{links}[/] [number]{cur(self.amount)}[/]'.strip()
        else: return f'{self.date} {self.entry.flag} {payee} {narration} {tags} {links} {cur(self.amount)}'.strip()

    def print_tags(self):
        tags = ''
        for tag in self.entry.tags: tags += f' #{tag}'
        return tags

    def print_links(self):
        links = ''
        for link in self.entry.links: links += f' ^{link}'
        return links

    def total(self):
        self.amount = 0.0
        for posting in self.entry.postings:
            self.amount += float(posting.units.number) if posting.units and posting.units.number > 0 else 0.0
        # self.remaining = self.limit - self.amount

    def add_posting(self, posting):
        post_i = -1
        post_amount = Decimal(posting['amount'])
        for i, post in enumerate(self.entry.postings):
            if post.account == posting['account']:
                post_i = i
                post_amount += post.units.number
                break
        new_post = Posting(posting["account"], Amount(post_amount, posting["currency"]), None, None, None, None)
        if post_i >= 0: self.entry.postings[post_i] = new_post
        else: self.entry.postings.append(new_post)
        self.total()

def ledger_load(console, ledger_path):
    try:
        entries, errors, options = loader.load_file(ledger_path)
        return Ledger(entries, errors, options)
    except FileNotFoundError:
        console.print(f"[error]Error: File {ledger_path} not found[/]")
        return None
    except Exception as e:
        console.print(f"[error]Error parsing Beancount file: {str(e)}[/]")
        return None

def ledger_bean(txn):
    return Bean(Transaction(None, txn.date, '*', txn.payee, '', [], [], []))
