from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.validation import Validator, ValidationError


class ValidOptions(Validator):
    def __init__(self, options):
        self.options = options

    def validate(self, document):
        text = document.text
        if text and text.lower() not in self.options:
            raise ValidationError(message="Please enter a valid response")

def valid_resolve(text):
    valid_text = ["r", "reconcile", "i", "insert", "s", "skip"]
    if text.lower() in valid_text: return True
    else: return False

resolve_validator = Validator.from_callable(
    valid_resolve,
    error_message="Please enter a valid response",
    move_cursor_to_end=True
)

def valid_confirm(text):
    valid_text = ['y', 'n']
    if text.lower() in valid_text: return True
    else: return False

confirm_validator = Validator.from_callable(
    valid_confirm,
    error_message="Please enter a valid response",
    move_cursor_to_end=True
)

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

def confirm_toolbar():
    return f"[Y]es  [N]o"
