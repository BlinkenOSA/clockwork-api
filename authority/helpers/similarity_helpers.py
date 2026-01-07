import unicodedata


def fold(s: str) -> str:
    """
    Normalizes a string for accent-insensitive comparison.

    Steps:
        - Applies Unicode NFKD normalization
        - Removes diacritics by ASCII encoding
        - Converts to lowercase
        - Strips leading/trailing whitespace

    Example:
        "János Kádár" → "janos kadar"

    Args:
        s: Input string.

    Returns:
        Folded, ASCII-only, lowercase string.
    """

    return (
        unicodedata.normalize('NFKD', s or '')
        .encode('ascii', 'ignore')
        .decode('ascii')
        .lower()
        .strip()
    )


def _trigrams(s: str):
    """
    Generates character trigrams with padding.

    Padding preserves edge information so that beginnings and endings
    of strings influence the hash.

    Example:
        "abc" → ["  a", " ab", "abc", "bc ", "c  "]

    Args:
        s: Input string.

    Returns:
        List of 3-character substrings.
    """

    s = f"  {s}  "  # padding to keep edges informative
    return [s[i:i+3] for i in range(len(s) - 2)]


def _hash64(s: str) -> int:
    """
    Computes a fast, non-cryptographic 64-bit hash of a string.

    This function is inspired by splitmix-style mixing and is designed
    to be:
        - fast
        - stable
        - evenly distributed

    It is *not* suitable for cryptographic purposes.

    Args:
        s: Input string.

    Returns:
        Unsigned 64-bit integer hash.
    """

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
    """
    Computes a 64-bit SimHash fingerprint for a string.

    Implementation details:
        - Uses character 3-grams as features
        - Hashes each trigram with `_hash64`
        - Aggregates bit votes across all trigrams
        - Produces a stable 64-bit fingerprint

    Properties:
        - Similar strings produce similar hashes
        - Hamming distance approximates string similarity
        - Extremely fast for large datasets

    Args:
        s: Input string (already folded/normalized if desired).

    Returns:
        Unsigned 64-bit SimHash fingerprint.
    """

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