"""
Similarity helpers for authority Person records.

This module implements a hybrid name-similarity search designed for
archival authority data, where spelling variants, transliteration,
initials, and partial names are common.

The algorithm combines multiple techniques:
    - Unicode folding and normalization
    - SimHash (Hamming-distance prefilter)
    - Regex-based token bucketing
    - RapidFuzz string similarity
    - Optional TF–IDF cosine similarity (character n-grams)

The output is a ranked list of Person objects with an additional
attribute `similarity_percent` (0–100), suitable for display in UI
components or duplicate-detection workflows.
"""

import re
from typing import List, Optional, Tuple
from django.db.models import Q, Value
from django.db.models.functions import Concat, Lower
from django.db.models.expressions import RawSQL
from rapidfuzz import fuzz

from authority.models import Person, fold, simhash64 as simhash64_fn

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")

def normalize_for_match(s: str) -> str:
    """
    Normalizes a string for similarity matching.

    Steps:
        - Removes punctuation
        - Normalizes whitespace
        - Lowercases the string

    Args:
        s: Input string.

    Returns:
        A normalized string suitable for fuzzy matching.
    """

    s = _PUNCT_RE.sub(" ", s or "")
    s = _WS_RE.sub(" ", s).strip().lower()
    return s

def first_token(s: str) -> str:
    """
    Returns the first whitespace-separated token of a string.

    Args:
        s: Input string.

    Returns:
        First token, or empty string if none exist.
    """

    toks = (s or "").split()
    return toks[0] if toks else ""

def last_token(s: str) -> str:
    """
    Returns the last whitespace-separated token of a string.

    Args:
        s: Input string.

    Returns:
        Last token, or empty string if none exist.
    """

    toks = (s or "").split()
    return toks[-1] if toks else ""

def _full_expr():
    """
    Returns a database expression concatenating first and last name.

    Used for annotating querysets with a searchable full-name field.
    """

    return Lower(Concat('first_name', Value(' '), 'last_name'))

def _initials_boost(target_norm: str, cand_norm: str) -> int:
    """
    Applies a small score boost when the target appears to be an initial.

    Example:
        "J Smith" vs "John Smith"

    Args:
        target_norm: Normalized target string.
        cand_norm: Normalized candidate string.

    Returns:
        Integer boost value (0 or small positive number).
    """

    t_first = first_token(target_norm)
    c_first = first_token(cand_norm)
    if len(t_first) == 1 and c_first.startswith(t_first):
        return 8
    return 0

def _mononym_boost(single: str, cand_norm: str) -> int:
    """
    Applies score boosts for single-token (mononym) queries.

    Boosts when the single token:
        - Matches exactly the first or last token
        - Prefix-matches the first or last token

    Args:
        single: Normalized single-token query.
        cand_norm: Normalized candidate name.

    Returns:
        Integer boost value.
    """

    f = first_token(cand_norm)
    l = last_token(cand_norm)
    boost = 0
    if single == f or single == l:
        boost += 10
    if f.startswith(single) or l.startswith(single):
        boost += 6
    return boost

def similar_people(
    target_full_name: str,
    *,
    exclude_id: Optional[int] = None,
    limit: int = 10,
    min_similarity: float = 0.2,   # threshold on final 0..1 scale
    max_candidates: int = 4000,
    max_hamming: int = 8,          # SimHash radius (for multi-token queries)
    w_tfidf: float = 0.55,         # blend weights
    w_fuzz: float = 0.45,
) -> List[Person]:
    """
    Finds Person records similar to the given full name.

    The function dynamically chooses one of two strategies based on
    token count:

    SINGLE-TOKEN QUERIES
    --------------------
    - Uses regex word-boundary matching and prefix buckets
    - Ranks candidates using RapidFuzz (WRatio / partial_ratio)
    - Applies mononym-specific boosts

    MULTI-TOKEN QUERIES
    ------------------
    - Uses SimHash (Hamming distance) as a prefilter
    - Widens candidates with last-token regex bucket
    - Ranks using a weighted blend of:
        * TF–IDF cosine similarity (char n-grams)
        * RapidFuzz similarity
    - Applies small boosts for initials and last-token matches

    Args:
        target_full_name:
            The input name to search for.

        exclude_id:
            Optional Person ID to exclude from results (useful for
            deduplication workflows).

        limit:
            Maximum number of results to return.

        min_similarity:
            Minimum similarity threshold on a 0–1 scale.

        max_candidates:
            Upper bound on candidate pool size before scoring.

        max_hamming:
            Maximum SimHash Hamming distance for multi-token queries.

        w_tfidf:
            Weight of TF–IDF similarity in final score.

        w_fuzz:
            Weight of RapidFuzz similarity in final score.

    Returns:
        A list of Person objects, each annotated with:
            - similarity_percent (int, 0–100)
    """

    target_raw = (target_full_name or "").strip()
    if not target_raw:
        return []

    t_folded = fold(target_raw)
    t_norm   = normalize_for_match(t_folded)
    toks     = t_norm.split()
    qs_base  = Person.objects.all()
    if exclude_id:
        qs_base = qs_base.exclude(id=exclude_id)

    # ---------- SINGLE-TOKEN PATH ----------
    if len(toks) == 1:
        single = toks[0]

        # Union of cheap, robust buckets:
        # 1) word-boundary match in full_name_folded (handles “Vladimir Lenin”)
        # 2) first_name/last_name prefix (handles “Stal” → “Stalin”)
        word_boundary_regex = rf"(^|[^a-z0-9]){re.escape(single)}($|[^a-z0-9])"
        bucket = (
            qs_base.filter(full_name_folded__regex=word_boundary_regex)
            | qs_base.filter(first_name__istartswith=single)
            | qs_base.filter(last_name__istartswith=single)
        ).distinct()

        candidates = list(
            bucket.annotate(_full=_full_expr()).values(
                'id','first_name','last_name','_full',
                'wikidata_id','wiki_url','authority_url','other_url'
            )[:max_candidates]
        )

        # Rank: RapidFuzz (WRatio/partial) + optional small TF-IDF if you keep it
        # (We can skip TF-IDF for single-token: it doesn’t add much. If you want it,
        # reuse your TF-IDF block on [t_norm] + candidates’ _full.)
        results: List[Tuple[int, dict]] = []
        cutoff = int(round(min_similarity * 100))

        for row in candidates:
            full_raw  = (row['_full'] or '').strip().lower()
            full_norm = normalize_for_match(full_raw)

            rf_wr = fuzz.WRatio(t_norm, full_norm)
            rf_pr = fuzz.partial_ratio(t_norm, full_norm)
            rf    = max(rf_wr, rf_pr)

            score = rf  # simple & effective for mononyms
            score += _mononym_boost(single, full_norm)

            score = int(round(max(0, min(100, score))))
            if score >= cutoff:
                results.append((score, row))

        results.sort(key=lambda x: x[0], reverse=True)
        results = results[:limit]

        ids = [r['id'] for _, r in results]
        people = {p.id: p for p in Person.objects.filter(id__in=ids)}
        out: List[Person] = []
        for score, row in results:
            p = people.get(row['id'])
            if p:
                p.similarity_percent = score
                out.append(p)
        return out

    # ---------- MULTI-TOKEN PATH (your existing hybrid) ----------
    # Keep your SimHash prefilter OR last-token bucket, then TF-IDF + RapidFuzz blend.
    t_hash = simhash64_fn(t_folded)
    t_last = last_token(t_norm)

    qs_simhash = qs_base.annotate(
        _dist=RawSQL("BIT_COUNT(CAST(simhash64 AS UNSIGNED) ^ %s)", (t_hash,))
    ).filter(_dist__lte=max_hamming)

    # Widen with a last-token bucket so initials/fullname issues get in
    last_bucket = qs_base.filter(full_name_folded__regex=rf"(^|[^a-z0-9]){re.escape(t_last)}($|[^a-z0-9])") if t_last else qs_base.none()
    union_qs = (qs_simhash | last_bucket).distinct()

    candidates = list(
        union_qs.annotate(_full=_full_expr()).values(
            'id','first_name','last_name','_full',
            'wikidata_id','wiki_url','authority_url','other_url'
        )[:max_candidates]
    )

    # Optional TF-IDF (char 3–5) on small candidate set
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        docs = [t_norm] + [normalize_for_match((r['_full'] or '').lower()) for r in candidates]
        vec = TfidfVectorizer(analyzer='char', ngram_range=(3,5), lowercase=False, norm='l2')
        X = vec.fit_transform(docs)
        tfidf_sims = cosine_similarity(X[0:1], X[1:])[0]  # 0..1
    except Exception:
        tfidf_sims = [0.0] * len(candidates)

    results: List[Tuple[int, dict]] = []
    cutoff = int(round(min_similarity * 100))

    for (idx, row) in enumerate(candidates):
        full_norm = normalize_for_match((row['_full'] or '').lower())

        rf_wr = fuzz.WRatio(t_norm, full_norm)
        rf_pr = fuzz.partial_ratio(t_norm, full_norm)
        rf    = max(rf_wr, rf_pr)

        tfidf = tfidf_sims[idx] * 100.0
        score = w_tfidf * tfidf + w_fuzz * rf

        # initials micro-boost
        score += _initials_boost(t_norm, full_norm)

        # last token exact match micro-boost
        if t_last and last_token(full_norm) == t_last:
            score += 3

        score = int(round(max(0, min(100, score))))
        if score >= cutoff:
            results.append((score, row))

    results.sort(key=lambda x: x[0], reverse=True)
    results = results[:limit]

    ids = [r['id'] for _, r in results]
    people = {p.id: p for p in Person.objects.filter(id__in=ids)}
    out: List[Person] = []
    for score, row in results:
        p = people.get(row['id'])
        if p:
            p.similarity_percent = score
            out.append(p)
    return out
