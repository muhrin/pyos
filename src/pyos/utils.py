import os


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 100
