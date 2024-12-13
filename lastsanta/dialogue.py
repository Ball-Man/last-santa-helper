import desper
from ddesigner import from_file


class DialogueHandle(desper.Handle):
    """Handle for dialogue resources."""

    def __init__(self, filename):
        self.filename = filename

    def load(self):
        with open(self.filename) as fin:
            return from_file(fin)
