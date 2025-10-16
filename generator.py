# src/generator.py
import secrets

UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?/`~\"'\\"

def build_alphabet(use_upper: bool, use_lower: bool, use_digits: bool, use_symbols: bool,
                   custom: str = "", replace_only: bool = False) -> str:
    if replace_only:
        pool = custom
    else:
        pool = ""
        if use_upper: pool += UPPER
        if use_lower: pool += LOWER
        if use_digits: pool += DIGITS
        if use_symbols: pool += SYMBOLS
        if custom:
            pool += custom
    # remove duplicates while preserving order
    seen = set()
    out = []
    for ch in pool:
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return "".join(out)

def generate_password(length: int, alphabet: str) -> str:
    if not alphabet:
        raise ValueError("Алфавит пуст")
    return "".join(secrets.choice(alphabet) for _ in range(length))
