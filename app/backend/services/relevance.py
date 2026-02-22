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
    "ekran şüşə",
    # Cables, chargers, adapters
    "kabel", "cable", "cord", "adapter", "adaptör",
    "şarj", "charger", "naqil", "şnur",
    # Accessories generic
    "aksesuar", "aksessuar", "accessory", "accessories",
    # Holders, stands, mounts
    "tutacaq", "holder", "stand", "mount", "tripod",
    # Stickers, skins
    "sticker", "yapışqan", "skin", "decal",
    # Straps, bands
    "strap", "qayış", "band",
    # Bags
    "çanta",
})

# Words indicating "this product is FOR something" (not the thing itself).
# Token-matched (exact) to avoid substring false positives ("for" ⊄ "format").
FOR_WORDS = frozenset({"üçün", "для", "for", "uchun"})


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens, dropping empties."""
    return [t for t in re.split(r'[\s\-/,.()\[\]]+', text.lower().strip()) if t]


def score_relevance(query: str, product_name: str) -> float:
    """Score 0.0–1.0 how relevant a product is to the search query.

    Three signals:
    1. Query-word match ratio   — what fraction of query words appear
       in the product name (substring match for morphology).
    2. Accessory penalty        — product contains accessory words that
       the query does NOT → score × 0.1.
    3. "For" penalty            — product says "üçün" / "for" but query
       doesn't → score × 0.2.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0

    product_lower = product_name.lower()
    query_lower = query.lower()

    # 1. Query-word match ratio
    matched = sum(1 for t in query_tokens if t in product_lower)
    score = matched / len(query_tokens)

    # 2. Accessory penalty (substring match handles suffixes)
    query_has_accessory = any(w in query_lower for w in ACCESSORY_WORDS)
    product_has_accessory = any(w in product_lower for w in ACCESSORY_WORDS)

    if product_has_accessory and not query_has_accessory:
        score *= 0.1

    # 3. "For" indicator penalty (exact token match)
    product_tokens = set(_tokenize(product_lower))
    query_tokens_set = set(query_tokens)

    product_has_for = bool(product_tokens & FOR_WORDS)
    query_has_for = bool(query_tokens_set & FOR_WORDS)

    if product_has_for and not query_has_for:
        score *= 0.2

    return score


def filter_relevant(
    products: list,
    query: str,
    min_score: float = 0.25,
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
        if score_relevance(query, p.product_name) >= min_score
    ]
