"""Relevance scoring and filtering for search results.

Solves the core problem: searching "iPhone 17 Pro 256 gray" should NOT
return phone cases, screen protectors, or cables — only actual phones.
"""

import re

# ── Accessory / peripheral indicator words ──
# Azerbaijani, Turkish, English, Russian — substring-matched against
# the product name to handle morphological suffixes (çexol → çexollar).
ACCESSORY_WORDS = frozenset({
    # Cases & covers
    "çexol", "keys", "case", "cover", "qab", "kabura",
    "kılıf", "bumper", "sleeve", "pouch",
    # Screen protectors
    "qoruyucu", "koruyucu", "protector", "tempered",
    "ekran şüşə", "glass", "film", "plyonka", "plyonka",
    # Cables, chargers, adapters
    "kabel", "cable", "cord", "adapter", "adaptör",
    "şarj", "charger", "naqil", "şnur",
    # Accessories generic
    "aksesuar", "aksessuar", "accessory", "accessories",
    # Holders, stands, mounts
    "tutacaq", "holder", "stand", "mount", "tripod",
    "kronşteyn",
    # Stickers, skins
    "sticker", "yapışqan", "skin", "decal",
    # Straps, bands
    "strap", "qayış", "band",
    # Bags & carry
    "çanta", "bag", "sumka",
    # Other peripherals
    "stylus", "qələm",
    "hub", "dock", "dongle",
})

# Words indicating "this product is FOR something" (not the thing itself).
# Token-matched (exact) to avoid substring false positives ("for" ⊄ "format").
FOR_WORDS = frozenset({"üçün", "для", "for", "uchun"})


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens, dropping empties."""
    return [t for t in re.split(r'[\s\-/,.()\[\]]+', text.lower().strip()) if t]


def _token_matches(token: str, product_lower: str, product_tokens: set[str]) -> bool:
    """Check if a query token matches in the product name.

    - Numeric tokens (e.g. "15", "256"): exact token match, OR prefix
      match with non-digit suffix (so "512" matches "512gb" but not "5120").
    - Short tokens (≤2 chars, e.g. "s", "se"): exact token match only.
      Prevents false positives on very short substrings.
    - Longer tokens: substring match to handle morphological suffixes
      (e.g. "samsung" matches "samsungun").
    """
    if token.isdigit():
        for pt in product_tokens:
            if pt == token:
                return True
            # "512" matches "512gb" but not "5120"
            if (pt.startswith(token)
                    and len(pt) > len(token)
                    and not pt[len(token)].isdigit()):
                return True
        return False
    if len(token) <= 2:
        return token in product_tokens
    return token in product_lower


def score_relevance(query: str, product_name: str, product_category: str | None = None) -> float:
    """Score 0.0–1.0 how relevant a product is to the search query.

    Five signals:
    1. Query-word match ratio   — what fraction of query words appear
       in the product name.
    2. Accessory penalty        — product contains accessory words that
       the query does NOT → score × 0.1.
    3. "For" penalty            — product says "üçün" / "for" but query
       doesn't → score × 0.2.
    4. Noise penalty            — product name has many extra tokens
       unrelated to the query → score × 0.6.
    5. Numeric mismatch penalty — model numbers and specs (e.g. "17",
       "512") are critical identifiers; missing matches → heavy penalty.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    product_lower = product_name.lower()

    # Hard category filter: if a category is set and has exclude_words,
    # any match means this product is completely irrelevant.
    if product_category and product_category not in ("all", "accessory"):
        from app.backend.services.category_detector import CATEGORIES

        cat = CATEGORIES.get(product_category)
        if cat and cat.exclude_words:
            if any(w in product_lower for w in cat.exclude_words):
                return 0.0
    product_tokens = set(_tokenize(product_lower))
    query_lower = query.lower()

    # 1. Query-word match ratio (smart matching)
    matched = sum(
        1 for t in query_tokens
        if _token_matches(t, product_lower, product_tokens)
    )
    score = matched / len(query_tokens)

    # 2. Accessory penalty (substring match handles suffixes)
    query_has_accessory = any(w in query_lower for w in ACCESSORY_WORDS)
    product_has_accessory = any(w in product_lower for w in ACCESSORY_WORDS)

    if product_has_accessory and not query_has_accessory:
        score *= 0.1

    # 3. "For" indicator penalty (exact token match)
    query_tokens_set = set(query_tokens)

    product_has_for = bool(product_tokens & FOR_WORDS)
    query_has_for = bool(query_tokens_set & FOR_WORDS)

    if product_has_for and not query_has_for:
        score *= 0.2

    # 4. Noise penalty — if >70% of product tokens are unrelated to query,
    #    the product is likely a different item that shares a few keywords.
    if matched > 0 and len(product_tokens) > 3:
        related = sum(
            1 for pt in product_tokens
            if any(qt in pt or pt in qt for qt in query_tokens)
        )
        noise_ratio = 1 - (related / len(product_tokens))
        if noise_ratio > 0.7:
            score *= 0.6

    # 5. Numeric mismatch penalty — numbers are the strongest identifiers
    #    (model numbers, storage, RAM). If they don't match, the product
    #    is almost certainly a different model/spec.
    numeric_query = [t for t in query_tokens if t.isdigit()]
    if numeric_query:
        numeric_matched = sum(
            1 for t in numeric_query
            if _token_matches(t, product_lower, product_tokens)
        )
        if numeric_matched == 0:
            # No numbers match at all — wrong model entirely
            score *= 0.1
        elif numeric_matched < len(numeric_query):
            # Some numbers match — partially wrong spec
            score *= 0.5

    return score


def filter_relevant(
    products: list,
    query: str,
    min_score: float = 0.4,
    product_category: str | None = None,
) -> list:
    """Filter out irrelevant products and keep sorting by price.

    - Products scoring below *min_score* are dropped.
    - Remaining products stay sorted by price (ascending).
    - If nothing passes the threshold, returns an empty list
      (this is intentional — for alerts we do NOT want to trigger
      on irrelevant accessories).
    """
    if not products:
        return products

    return [
        p for p in products
        if score_relevance(query, p.product_name, product_category) >= min_score
    ]
