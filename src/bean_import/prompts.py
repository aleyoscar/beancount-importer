from prompt_toolkit.validation import Validator
from prompt_toolkit.key_binding import KeyBindings

def valid_resolve(text):
    valid_text = ["r", "reconcile", "i", "insert", "s", "skip"]
    if text in valid_text: return True
    else: return False

resolve_validator = Validator.from_callable(
    valid_resolve,
    error_message="Please enter a valid response",
    move_cursor_to_end=True
)

cancel_bindings = KeyBindings()

@cancel_bindings.add("c-x")
def _(event):
    " To cancel press `c-x`. "
    event.app.exit()

def resolve_toolbar():
    return f"[R]econcile  [I]nsert  [S]kip"

def cancel_toolbar():
    return f"[c-x] to Cancel"
