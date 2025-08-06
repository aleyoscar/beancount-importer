from .helpers import cur
from ofxparse import OfxParser
from datetime import datetime

class Transaction:
    def __init__(self, id="", date=datetime.today(), payee="", amount=0.0):
        self.id = id
        self.date = date.strftime('%Y-%m-%d')
        self.payee = payee

        self.amount = float(amount)
        self.year = int(self.date.split('-')[0])

    def __str__(self):
        return f'{self.date} {self.payee} {cur(self.amount)}'

    def print(self, theme=False):
        if theme: return f'[date]{self.date}[/] [string]{self.payee}[/] [number]{cur(self.amount)}[/]'
        else: return self.__str__

def ofx_load(console, ofx_path):
    try:
        # Open and parse the OFX file
        with open(ofx_path, 'r') as file:
            ofx = OfxParser.parse(file)

        # Extract account information
        account = ofx.account
        account_info = {
            'account_id': account.account_id,
            'account_type': account.account_type,
            'institution': account.institution.organization if account.institution else 'Unknown'
        }

        # Extract transactions
        transactions = [Transaction(id=t.id, date=t.date, payee=t.payee, amount=t.amount) for t in account.statement.transactions]

        return {
            'account_info': account_info,
            'transactions': transactions
        }

    except FileNotFoundError:
        console.print(f"[error]Error: File {ofx_path} not found.[/]")
        return None
    except Exception as e:
        console.print(f"[error]Error parsing OFX file: {str(e)}[/]")
        return None

def ofx_pending(txns, beans, account):
    pending = []
    for txn in txns:
        found = False
        for bean in beans:
            if 'account' in bean.entry.meta and 'id' in bean.entry.meta:
                if bean.entry.meta['id'] == txn.id and bean.entry.meta['account'] == account:
                    found = True
                    break
        if not found:
            pending.append(txn)
    return pending
