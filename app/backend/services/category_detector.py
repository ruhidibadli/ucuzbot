"""Product category detection for search filtering.

Detects product categories from search queries so that post-scrape
relevance filtering can hard-exclude irrelevant products (e.g. phone
cases when the user is searching for an actual phone).
"""

from dataclasses import dataclass, field

from app.backend.services.relevance import ACCESSORY_WORDS


@dataclass(frozen=True)
class ProductCategory:
    slug: str
    name_az: str
    emoji: str
    trigger_keywords: tuple[str, ...] = ()
    exclude_words: frozenset[str] = field(default_factory=frozenset)


# ── Extra domain words to exclude per category ──

_PHONE_TERMS = frozenset({"telefon", "smartfon", "iphone", "samsung", "xiaomi", "redmi", "poco", "pixel", "huawei", "honor", "oneplus"})
_LAPTOP_TERMS = frozenset({"laptop", "noutbuk", "notebook", "macbook", "thinkpad", "ideapad", "vivobook", "zenbook"})
_TV_TERMS = frozenset({"televizor", "tv", "oled", "qled"})
_TABLET_TERMS = frozenset({"planset", "tablet", "ipad", "galaxy tab"})
_HEADPHONE_WORDS = frozenset({"qulaqliq", "nausnik", "headphone", "earbuds", "buds", "airpods"})

# Headphones are accessories themselves, so remove headphone words from the accessory set
_ACCESSORY_WORDS_NO_HEADPHONES = ACCESSORY_WORDS - _HEADPHONE_WORDS


# ── Category registry ──

CATEGORIES: dict[str, ProductCategory] = {
    "phone": ProductCategory(
        slug="phone",
        name_az="Telefon",
        emoji="\U0001f4f1",
        trigger_keywords=(
            "iphone", "samsung galaxy", "xiaomi", "redmi", "poco",
            "pixel", "huawei", "honor", "oneplus", "telefon", "smartfon",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "laptop": ProductCategory(
        slug="laptop",
        name_az="Noutbuk",
        emoji="\U0001f4bb",
        trigger_keywords=(
            "macbook", "laptop", "noutbuk", "notebook",
            "thinkpad", "ideapad", "vivobook", "zenbook",
        ),
        exclude_words=ACCESSORY_WORDS | _PHONE_TERMS | _TV_TERMS | _TABLET_TERMS,
    ),
    "tv": ProductCategory(
        slug="tv",
        name_az="Televizor",
        emoji="\U0001f4fa",
        trigger_keywords=("televizor", "tv", "oled", "qled"),
        exclude_words=ACCESSORY_WORDS | _PHONE_TERMS | _LAPTOP_TERMS | _TABLET_TERMS,
    ),
    "tablet": ProductCategory(
        slug="tablet",
        name_az="Planset",
        emoji="\U0001f4f1",
        trigger_keywords=("ipad", "planset", "tablet", "galaxy tab"),
        exclude_words=ACCESSORY_WORDS | _PHONE_TERMS | _LAPTOP_TERMS | _TV_TERMS,
    ),
    "headphones": ProductCategory(
        slug="headphones",
        name_az="Qulaqliq",
        emoji="\U0001f3a7",
        trigger_keywords=(
            "airpods", "qulaqliq", "nausnik", "headphone",
            "earbuds", "buds", "jbl",
        ),
        exclude_words=_ACCESSORY_WORDS_NO_HEADPHONES,
    ),
    "console": ProductCategory(
        slug="console",
        name_az="Oyun Konsolu",
        emoji="\U0001f3ae",
        trigger_keywords=(
            "playstation", "ps5", "ps4", "xbox", "nintendo", "switch",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "appliance": ProductCategory(
        slug="appliance",
        name_az="M\u0259is\u0259t Texnikas\u0131",
        emoji="\U0001f3e0",
        trigger_keywords=(
            "paltaryuyan", "soyuducu", "kondisioner",
            "tozsoran", "qabyuyan",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "main_product": ProductCategory(
        slug="main_product",
        name_az="\u018esas m\u0259hsul",
        emoji="\U0001f3f7\ufe0f",
        trigger_keywords=(),
        exclude_words=ACCESSORY_WORDS,
    ),
    "accessory": ProductCategory(
        slug="accessory",
        name_az="Aksessuar",
        emoji="\U0001f4e6",
        trigger_keywords=(),
        exclude_words=frozenset(),
    ),
    "all": ProductCategory(
        slug="all",
        name_az="Ham\u0131s\u0131",
        emoji="\U0001f50d",
        trigger_keywords=(),
        exclude_words=frozenset(),
    ),
}


def detect_categories(query: str) -> list[ProductCategory]:
    """Detect matching product categories from a search query.

    Returns a list of 2-4 ProductCategory items:
    - Detected category (if any) or ``main_product`` as fallback
    - ``accessory`` (always)
    - ``all`` (always)

    Longer / more-specific trigger keywords are checked first so that
    e.g. "galaxy tab" matches *tablet* before "galaxy" could match *phone*.
    """
    query_lower = query.lower()

    # Build (keyword, category) pairs sorted by keyword length descending
    # so longer/more-specific patterns are matched first.
    keyword_pairs: list[tuple[str, ProductCategory]] = []
    for cat in CATEGORIES.values():
        for kw in cat.trigger_keywords:
            keyword_pairs.append((kw, cat))
    keyword_pairs.sort(key=lambda pair: len(pair[0]), reverse=True)

    detected: list[ProductCategory] = []
    seen_slugs: set[str] = set()

    for kw, cat in keyword_pairs:
        if cat.slug in seen_slugs:
            continue
        if kw in query_lower:
            detected.append(cat)
            seen_slugs.add(cat.slug)

    # Fallback when nothing detected
    if not detected:
        detected.append(CATEGORIES["main_product"])

    # Always append accessory and all
    detected.append(CATEGORIES["accessory"])
    detected.append(CATEGORIES["all"])

    return detected
