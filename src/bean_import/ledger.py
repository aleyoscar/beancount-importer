from beancount import loader
from beancount.core.data import Transaction
from beancount.parser import printer
from .helpers import cur

class Bean:
    def __init__(self, entry):
        self.entry = entry
        """
        meta:       dict[str, Any]
        date:       date
        flag:       str
        payee:      Optional[str]
        narration:  Optional[str]
        tags:       frozenset[str]
        links:      frozenset[str]
        postings:   list[
            account:    str
            units:      Optional[Amount[
                number:     float
                currency:   str
            ]]
            cost:       Union[Cost, CostSpec]
            price:      Optional[Amount]
            flag:       Optional[str]
            meta:       Optional[dict[str, Any]]
        ]
        """
        self.date = entry.date.strftime('%Y-%m-%d')
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

    # def add_posting(self, amount, account):
    #     # if account in self.postings: self.postings[account] += float(amount)
    #     # else: self.postings[account] = float(amount)
    #     self.total()
    #
    # def reset_postings(self):
    #     # self.postings = {}
    #     self.total()

        # new_entry = Transaction(meta, date, flag, payee, narration, tags, links, postings)

def ledger_load(console, ledger_path):
    try:
        entries, errors, options = loader.load_file(ledger_path)
        account_info = {
            'title': options.get('title', 'Unknown'),
            'operating_currency': options.get('operating_currency', [])
        }

        return {
            'account_info': account_info,
            'transactions': [Bean(t) for t in entries if isinstance(t, Transaction)],
            'errors': [str(err) for err in errors] if errors else []
        }

    except FileNotFoundError:
        console.print(f"[error]Error: File {ledger_path} not found[/]")
        return None
    except Exception as e:
        console.print(f"[error]Error parsing Beancount file: {str(e)}[/]")
        return None
