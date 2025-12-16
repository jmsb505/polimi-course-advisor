from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, Set


# Very small, hand-written stopword list (English + some Italian articles/prepositions)
_STOPWORDS = {
    # English
    "and", "or", "the", "a", "an", "for", "of", "in", "on", "to", "with",
    "by", "from", "at", "is", "are", "be",
    # Italian-ish
    "di", "la", "il", "lo", "le", "i", "gli", "un", "una", "uno",
    "degli", "delle", "dei", "del", "della", "dell",
}

_WORD_RE = re.compile(r"[a-zA-ZÀ-ÖØ-öø-ÿ0-9]+")


def tokenize(text: str) -> Set[str]:
    """
    Lowercase + simple regex split + stopword removal.
    Returns a set of tokens.
    """
    text = text.lower()
    tokens = _WORD_RE.findall(text)
    
    # Naive stemming to handle basic plurals
    def _naive_stem(w: str) -> str:
        if w.endswith("s") and len(w) > 3:
            return w[:-1]
        return w

    result = set()
    for t in tokens:
        if t in _STOPWORDS:
            continue
        if len(t) < 2:
            continue
        result.add(_naive_stem(t))
    return result


@lru_cache(maxsize=2048)
def tokens_from_name_and_description(name: str, description: str) -> Set[str]:
    """
    Cached tokenization for 'name + description' pairs, used in graph and ranking.
    """
    return tokenize(f"{name} {description}")


def tokens_from_phrase(phrase: str) -> Set[str]:
    """
    Tokenize a short free-text phrase (interest, goal, etc.).
    """
    return tokenize(phrase)


def jaccard_similarity(a: Set[str], b: Set[str]) -> float:
    """
    Jaccard similarity between two token sets, in [0, 1].
    """
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    union = len(a | b)
    return inter / union


def contains_any(tokens: Set[str], query_tokens: Iterable[str]) -> bool:
    """
    True if any of the query tokens is contained in the token set.
    """
    for q in query_tokens:
        if q in tokens:
            return True
    return False
