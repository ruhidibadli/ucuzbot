from enum import StrEnum


class StoreSlug(StrEnum):
    KONTAKT = "kontakt"
    BAKU_ELECTRONICS = "baku_electronics"
    IRSHAD = "irshad"
    MAXI = "maxi"
    TAP_AZ = "tap_az"
    UMICO = "umico"


class SubscriptionTier(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


STORE_CONFIGS = {
    StoreSlug.KONTAKT: {
        "name": "Kontakt Home",
        "base_url": "https://kontakt.az",
        "search_url_template": "https://kontakt.az/catalogsearch/result/?q={query}",
        "scraper_class": "KontaktScraper",
    },
    StoreSlug.BAKU_ELECTRONICS: {
        "name": "Baku Electronics",
        "base_url": "https://www.bakuelectronics.az",
        "search_url_template": "https://www.bakuelectronics.az/axtaris-neticesi?name={query}",
        "scraper_class": "BakuElectronicsScraper",
    },
    StoreSlug.IRSHAD: {
        "name": "Irshad",
        "base_url": "https://irshad.az",
        "search_url_template": "https://irshad.az/az/products/list?q={query}",
        "scraper_class": "IrshadScraper",
    },
    StoreSlug.MAXI: {
        "name": "Maxi.az",
        "base_url": "https://maxi.az",
        "search_url_template": "https://maxi.az/axtaris?q={query}",
        "scraper_class": "MaxiScraper",
    },
    StoreSlug.TAP_AZ: {
        "name": "Tap.az",
        "base_url": "https://tap.az",
        "search_url_template": "https://tap.az/elanlar?keywords={query}",
        "scraper_class": "TapAzScraper",
    },
    StoreSlug.UMICO: {
        "name": "Birmarket",
        "base_url": "https://birmarket.az",
        "search_url_template": "https://birmarket.az/search?q={query}",
        "scraper_class": "UmicoScraper",
    },
}

DEFAULT_HEADERS = {
    "Accept-Language": "az,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CURRENCY_SYMBOL = "₼"
CURRENCY_CODE = "AZN"
