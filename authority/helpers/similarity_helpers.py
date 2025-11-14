import unicodedata


def fold(s: str) -> str:
    return (
        unicodedata.normalize('NFKD', s or '')
        .encode('ascii', 'ignore')
        .decode('ascii')
        .lower()
        .strip()
    )


# --- SimHash helpers (64-bit) over character 3-grams ---
def _trigrams(s: str):
    s = f"  {s}  "  # padding to keep edges informative
    return [s[i:i+3] for i in range(len(s) - 2)]


def _hash64(s: str) -> int:
    # a tiny, fast 64-bit non-cryptographic hash
    # (splitmix-like; good enough for SimHash purposes)
    x = 0x9E3779B97F4A7C15
    h = 0
    for ch in s:
        x ^= ord(ch)
        x = (x * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        x ^= (x >> 30)
        x = (x * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        h ^= x
    return h & 0xFFFFFFFFFFFFFFFF


def simhash64(s: str) -> int:
    # Character-3gram SimHash
    grams = _trigrams(s)
    if not grams:
        return 0
    bits = [0]*64
    for g in grams:
        h = _hash64(g)
        for i in range(64):
            bits[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i, val in enumerate(bits):
        if val >= 0:
            out |= (1 << i)
    return out & 0xFFFFFFFFFFFFFFFF