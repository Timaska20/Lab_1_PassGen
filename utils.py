# src/utils.py
import math

def estimate_entropy(alphabet_size: int, length: int) -> float:
    if alphabet_size <= 1 or length <= 0:
        return 0.0
    return length * math.log2(alphabet_size)
