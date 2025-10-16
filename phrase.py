# src/phrase.py
import hashlib
from typing import Optional

def normalize_text(*parts: str) -> str:
    """Собираем и нормализуем фразу (обрезаем, схлопываем пробелы)."""
    text = " ".join([p.strip() for p in parts if p and p.strip()])
    return " ".join(text.split())

def derive_bytes(seed_text: str, salt: Optional[str] = None, out_len: int = 64) -> bytes:
    """Детерминированные байты из seed (+ опц. соль) через BLAKE2b."""
    seed = (seed_text + (salt or "")).encode("utf-8", errors="ignore")
    # digest_size 32..64
    size = min(max(out_len, 32), 64)
    h = hashlib.blake2b(seed, digest_size=size)
    return h.digest()

def generate_password_from_seed(alphabet: str, length: int, seed_text: str, salt: Optional[str] = None) -> str:
    if not alphabet:
        raise ValueError("Алфавит пуст")
    if length <= 0:
        raise ValueError("Длина должна быть > 0")
    raw = derive_bytes(seed_text, salt=salt, out_len=max(64, length * 2))
    A = len(alphabet)
    out = []
    i = 0
    while len(out) < length:
        b = raw[i % len(raw)]
        out.append(alphabet[b % A])
        i += 1
    return "".join(out)
