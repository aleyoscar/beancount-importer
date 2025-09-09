from datetime import datetime
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.validation import Validator, ValidationError
import re

class ValidOptions(Validator):
    def __init__(self, options):
        self.options = options

    def validate(self, document):
        text = document.text
        if text and text.lower() not in self.options:
            raise ValidationError(message="Please enter a valid response")

def is_float(text):
    try:
        float(text)
        return True
    except ValueError:
        return False

def is_math_float(text):
    pattern = r'^(-?\d*\.?\d+)([+\-*/](-?\d*\.?\d+))*$'
    return bool(re.match(pattern, text))

def is_account(text):
    return bool(re.fullmatch(r"^(Assets|Liabilities|Capital|Income|Expenses):[A-Z][A-Za-z0-9-]*(:[A-Z][A-Za-z0-9-]*)*$", text))

def is_date(text):
    if not re.fullmatch(r'^(?!0000)[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$', text):
        return False
    try:
        year, month, day = map(int, text.split('-'))
        datetime(year, month, day)
        return True
    except ValueError:
        return False

def is_link_tag(text):
    for t in text.split():
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]*', t):
            return False
    return True

valid_float = Validator.from_callable(is_float, error_message="Not a valid number", move_cursor_to_end=True)
valid_math_float = Validator.from_callable(is_math_float, error_message="Not a valid number or expression", move_cursor_to_end=True)
valid_account = Validator.from_callable(is_account, error_message="Not a valid account", move_cursor_to_end=True)
valid_date = Validator.from_callable(is_date, error_message="Not a valid date", move_cursor_to_end=True)
valid_link_tag = Validator.from_callable(is_link_tag, error_message="Not a valid link or tag", move_cursor_to_end=True)

cancel_bindings = KeyBindings()

@cancel_bindings.add("c-x")
def _(event):
    " To cancel press `c-x`. "
    def print_cancel():
        print("...Canceling")
    event.app.exit()
    run_in_terminal(print_cancel)

def resolve_toolbar():
    return f"[R]econcile  [I]nsert  [S]kip  [Q]uit"

def cancel_toolbar():
    return f"[c-x] to Cancel"

def postings_toolbar(amt):
    return f"({amt}) left  [c-x] to Cancel"

def confirm_toolbar():
    return f"[Y]es  [N]o"

def edit_toolbar():
    return f"[D]ate  [F]lag  [P]ayee  [N]arration  [T]ags  [L]inks  P[O]stings  [S]ave  [c-x] Cancel"
