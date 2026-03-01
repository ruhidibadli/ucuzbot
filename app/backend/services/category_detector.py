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


# ── Cross-domain term sets for exclusion ──

_PHONE_TERMS = frozenset({
    "telefon", "smartfon", "iphone", "samsung", "xiaomi", "redmi",
    "poco", "pixel", "huawei", "honor", "oneplus",
})
_LAPTOP_TERMS = frozenset({
    "laptop", "noutbuk", "notebook", "macbook", "thinkpad",
    "ideapad", "vivobook", "zenbook",
})
_TV_TERMS = frozenset({"televizor", "tv", "oled", "qled"})
_TABLET_TERMS = frozenset({"planset", "tablet", "ipad", "galaxy tab"})
_HEADPHONE_WORDS = frozenset({
    "qulaqliq", "nausnik", "headphone", "earbuds", "buds", "airpods",
})

_ACCESSORY_WORDS_NO_HEADPHONES = ACCESSORY_WORDS - _HEADPHONE_WORDS


# ── Category registry ──

CATEGORIES: dict[str, ProductCategory] = {

    # ─── Electronics: Mobile & Computing ───

    "phone": ProductCategory(
        slug="phone",
        name_az="Telefon",
        emoji="\U0001f4f1",
        trigger_keywords=(
            "iphone", "samsung galaxy", "xiaomi", "redmi", "poco",
            "pixel", "huawei", "honor", "oneplus", "telefon", "smartfon",
            "nothing phone", "realme", "oppo", "vivo", "motorola", "nokia",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "laptop": ProductCategory(
        slug="laptop",
        name_az="Noutbuk",
        emoji="\U0001f4bb",
        trigger_keywords=(
            "macbook", "laptop", "noutbuk", "notebook", "matebook",
            "thinkpad", "ideapad", "vivobook", "zenbook",
            "rog strix", "legion", "pavilion", "inspiron",
            "surface laptop", "chromebook",
        ),
        exclude_words=ACCESSORY_WORDS | _PHONE_TERMS | _TV_TERMS | _TABLET_TERMS,
    ),
    "tablet": ProductCategory(
        slug="tablet",
        name_az="Plan\u015fet",
        emoji="\U0001f4f1",
        trigger_keywords=(
            "ipad", "planset", "plan\u015fet", "tablet", "galaxy tab",
            "surface pro", "surface go",
        ),
        exclude_words=ACCESSORY_WORDS | _PHONE_TERMS | _LAPTOP_TERMS | _TV_TERMS,
    ),
    "smartwatch": ProductCategory(
        slug="smartwatch",
        name_az="A\u011f\u0131ll\u0131 Saat",
        emoji="\u231a",
        trigger_keywords=(
            "apple watch", "galaxy watch", "smart watch", "smartwatch",
            "amazfit", "garmin", "fitbit", "huawei watch", "mi band",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "headphones": ProductCategory(
        slug="headphones",
        name_az="Qulaql\u0131q",
        emoji="\U0001f3a7",
        trigger_keywords=(
            "airpods", "qulaqliq", "qulaql\u0131q", "nausnik", "headphone",
            "earbuds", "buds", "jbl", "sony wh", "sony wf",
            "marshall", "bose", "sennheiser", "beats",
        ),
        exclude_words=_ACCESSORY_WORDS_NO_HEADPHONES,
    ),

    # ─── Electronics: Home & Entertainment ───

    "tv": ProductCategory(
        slug="tv",
        name_az="Televizor",
        emoji="\U0001f4fa",
        trigger_keywords=(
            "televizor", "oled", "qled", "smart tv",
            "samsung tv", "lg tv", "sony tv", "hisense", "tcl tv",
        ),
        exclude_words=ACCESSORY_WORDS | _PHONE_TERMS | _LAPTOP_TERMS | _TABLET_TERMS,
    ),
    "console": ProductCategory(
        slug="console",
        name_az="Oyun Konsolu",
        emoji="\U0001f3ae",
        trigger_keywords=(
            "playstation", "ps5", "ps4", "xbox", "nintendo",
            "nintendo switch", "steam deck",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "speaker": ProductCategory(
        slug="speaker",
        name_az="Dinamik / Kolonka",
        emoji="\U0001f50a",
        trigger_keywords=(
            "kolonka", "dinamik", "speaker", "soundbar", "subwoofer",
            "bluetooth speaker", "portativ kolonka",
            "jbl charge", "jbl flip", "jbl go", "jbl xtreme",
            "harman kardon", "marshall speaker", "bose speaker",
            "homepod", "echo", "yandex stansiyas\u0131",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "camera": ProductCategory(
        slug="camera",
        name_az="Kamera / Fotoaparat",
        emoji="\U0001f4f7",
        trigger_keywords=(
            "fotoaparat", "kamera", "camera", "canon eos", "nikon",
            "sony alpha", "fujifilm", "gopro", "dji", "drone",
            "action camera", "mirrorless", "dslr", "webcam",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),

    # ─── PC & Components ───

    "pc": ProductCategory(
        slug="pc",
        name_az="Komp\u00fcter",
        emoji="\U0001f5a5\ufe0f",
        trigger_keywords=(
            "komp\u00fcter", "komputer", "desktop", "masaustu",
            "masa \u00fcst\u00fc", "gaming pc", "imac", "mac mini",
            "mac studio", "mac pro", "mini pc",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "pc_component": ProductCategory(
        slug="pc_component",
        name_az="PC Komponent",
        emoji="\U0001f9e9",
        trigger_keywords=(
            "videokart", "video kart", "gpu", "rtx", "gtx", "radeon",
            "prosessor", "processor", "cpu", "ryzen", "intel core",
            "anakart", "ana kart", "motherboard",
            "operativ yaddas", "ram", "ddr4", "ddr5",
            "ssd", "hdd", "nvme", "m.2",
            "qida bloku", "power supply", "psu",
            "keys", "pc case", "komputer keysi",
            "kuler", "cooler", "su soyutma", "aio",
        ),
        exclude_words=frozenset(),  # Components are specific enough
    ),
    "monitor": ProductCategory(
        slug="monitor",
        name_az="Monitor",
        emoji="\U0001f5a5\ufe0f",
        trigger_keywords=(
            "monitor", "display", "gaming monitor",
            "ultrawide", "curved monitor",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "printer": ProductCategory(
        slug="printer",
        name_az="Printer / Skaner",
        emoji="\U0001f5a8\ufe0f",
        trigger_keywords=(
            "printer", "skaner", "scanner", "mfp", "lazer printer",
            "inkjet", "epson", "hp printer", "canon printer",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "networking": ProductCategory(
        slug="networking",
        name_az="Router / \u015e\u0259b\u0259k\u0259",
        emoji="\U0001f4e1",
        trigger_keywords=(
            "router", "modem", "wifi", "wi-fi", "mesh",
            "access point", "switch", "tp-link", "asus router",
            "mikrotik", "ubiquiti",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),

    # ─── Home & Appliances ───

    "appliance": ProductCategory(
        slug="appliance",
        name_az="M\u0259i\u015f\u0259t Texnikas\u0131",
        emoji="\U0001f3e0",
        trigger_keywords=(
            "paltaryuyan", "paltar yuyan", "soyuducu", "kondisioner",
            "tozsoran", "toz soran", "qabyuyan", "qab yuyan",
            "quruducu", "dondurucu", "su qizdirici", "kombi",
            "isidici", "pec", "plita", "soba",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "kitchen_appliance": ProductCategory(
        slug="kitchen_appliance",
        name_az="M\u0259tb\u0259x Texnikas\u0131",
        emoji="\U0001f373",
        trigger_keywords=(
            "blender", "mikser", "mixer", "toster", "toaster",
            "mikrodalga", "microwave", "qehve", "q\u0259hv\u0259",
            "coffee", "nespresso", "multicooker", "air fryer",
            "fritoz", "sokovijimalka", "juicer", "elektrik caynik",
            "kettle", "\u00e7aynik", "caydan", "sacayagi",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "furniture": ProductCategory(
        slug="furniture",
        name_az="Mebel",
        emoji="\U0001fa91",
        trigger_keywords=(
            "mebel", "divan", "kreslo", "stol", "stul",
            "skaf", "\u015fkaf", "dolab", "regal", "yataq",
            "carpayi", "\u00e7arpayi", "jurnal masasi", "komod",
            "tv alt\u0131", "kitab regal\u0131", "ofis stolu",
            "gaming stul", "gaming kreslo",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "lighting": ProductCategory(
        slug="lighting",
        name_az="I\u015f\u0131qland\u0131rma",
        emoji="\U0001f4a1",
        trigger_keywords=(
            "lampa", "lustur", "l\u00fcstr", "led lampa",
            "proyektor", "projector", "i\u015f\u0131q",
            "torser", "bra",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),

    # ─── Personal Care & Fashion ───

    "clothing": ProductCategory(
        slug="clothing",
        name_az="Geyim",
        emoji="\U0001f455",
        trigger_keywords=(
            "geyim", "kostyum", "k\u00f6yn\u0259k", "koynek",
            "pencek", "pen\u00e7\u0259k", "palto", "kurtka",
            "\u015falvar", "salvar", "cins", "jeans",
            "futbolka", "t-shirt", "tshirt", "sviter", "hoodie",
            "idman geyimi", "boxer", "boksyor", "alt paltari",
            "corab", "gelinlik", "don", "yubka", "etek",
        ),
        exclude_words=frozenset(),
    ),
    "shoes": ProductCategory(
        slug="shoes",
        name_az="Ayaqq\u0131b\u0131",
        emoji="\U0001f45f",
        trigger_keywords=(
            "ayaqqabi", "ayaqq\u0131b\u0131", "krossovka", "bot",
            "botin", "sandal", "tapochka", "nike", "adidas",
            "puma", "new balance", "reebok", "skechers", "converse",
            "jordan", "air max", "yeezy",
        ),
        exclude_words=frozenset(),
    ),
    "bags": ProductCategory(
        slug="bags",
        name_az="\u00c7anta",
        emoji="\U0001f45c",
        trigger_keywords=(
            "canta", "\u00e7anta", "ryukzak", "r\u00fckzak",
            "backpack", "bel \u00e7antas\u0131", "el \u00e7antas\u0131",
            "laptop \u00e7antas\u0131", "bavul", "chemodan", "\u00e7emodan",
        ),
        exclude_words=frozenset(),
    ),
    "watch": ProductCategory(
        slug="watch",
        name_az="Saat",
        emoji="\u231a",
        trigger_keywords=(
            "qol saati", "saat", "casio", "tissot",
            "rolex", "seiko", "orient", "fossil", "emporio armani",
            "daniel wellington", "g-shock",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),
    "perfume": ProductCategory(
        slug="perfume",
        name_az="\u018ftir / Parfum",
        emoji="\U0001f9f4",
        trigger_keywords=(
            "etir", "\u0259tir", "parfum", "perfume", "odekolon",
            "eau de parfum", "eau de toilette",
            "dior", "chanel", "gucci perfume", "versace",
            "tom ford", "creed",
        ),
        exclude_words=frozenset(),
    ),
    "beauty": ProductCategory(
        slug="beauty",
        name_az="G\u00f6z\u0259llik / Kosmetika",
        emoji="\U0001f484",
        trigger_keywords=(
            "kosmetika", "makiyaj", "krem", "serum",
            "maskara", "pomada", "ruj", "fondoten", "foundation",
            "toner", "sac boyasi", "sa\u00e7 boyas\u0131",
            "lak", "dus geli", "du\u015f geli", "sabun", "sampun",
            "\u015fampun", "sa\u00e7 quruduca", "fen", "utuleyici",
        ),
        exclude_words=frozenset(),
    ),
    "glasses": ProductCategory(
        slug="glasses",
        name_az="Eyn\u0259k",
        emoji="\U0001f576\ufe0f",
        trigger_keywords=(
            "eynek", "eyn\u0259k", "gunes eyneki",
            "g\u00fcn\u0259\u015f eyn\u0259yi", "optik eynek",
            "ray-ban", "rayban", "oakley",
        ),
        exclude_words=frozenset(),
    ),
    "jewelry": ProductCategory(
        slug="jewelry",
        name_az="Z\u0259rg\u0259rlik",
        emoji="\U0001f48d",
        trigger_keywords=(
            "uzuk", "\u00fcz\u00fck", "qolbaq", "boyunbagi",
            "boyunba\u011f\u0131", "sirga", "s\u0131rqa", "bilerzik",
            "bil\u0259rzik", "zergerlik", "z\u0259rg\u0259rlik",
            "qizil", "gumus", "g\u00fcm\u00fc\u015f",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Sports & Outdoors ───

    "sports": ProductCategory(
        slug="sports",
        name_az="\u0130dman",
        emoji="\u26bd",
        trigger_keywords=(
            "idman", "fitness", "trenajor", "qacan yolu",
            "qantel", "shtanqa", "yoga", "velosiped", "bicycle",
            "futbol topu", "basketbol", "tennis", "boks",
            "idman aletleri", "trenaj\u00f6r",
            "treadmill", "velotrena\u017eor",
        ),
        exclude_words=frozenset(),
    ),
    "outdoor": ProductCategory(
        slug="outdoor",
        name_az="Turizm / Outdoor",
        emoji="\u26fa",
        trigger_keywords=(
            "cadir", "\u00e7ad\u0131r", "tent", "yataq kisesi",
            "yuxu kisesi", "termos", "feneri", "kompas",
            "turist", "camping",
        ),
        exclude_words=frozenset(),
    ),
    "scooter": ProductCategory(
        slug="scooter",
        name_az="Skuter / Elektrikli",
        emoji="\U0001f6f4",
        trigger_keywords=(
            "skuter", "scooter", "elektrikli skuter",
            "elektrik velosiped", "segway", "hoverboard",
            "elektro samokat", "samokat",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),

    # ─── Kids & Baby ───

    "toys": ProductCategory(
        slug="toys",
        name_az="Oyuncaq",
        emoji="\U0001f9f8",
        trigger_keywords=(
            "oyuncaq", "lego", "kukla", "robot oyuncaq",
            "konstruktor", "puzzle", "pazzl",
            "barbie", "hot wheels", "nerf",
            "rc car", "uzaqdan idare",
        ),
        exclude_words=frozenset(),
    ),
    "baby": ProductCategory(
        slug="baby",
        name_az="U\u015faq M\u0259hsullar\u0131",
        emoji="\U0001f476",
        trigger_keywords=(
            "usaq arabaasi", "u\u015faq arabas\u0131", "stroller",
            "besik", "be\u015fik", "usaq yataqi", "u\u015faq yata\u011f\u0131",
            "mama sandalyesi", "usaq oturacagi",
            "pampers", "bez", "biberon", "emzik",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Auto & Vehicle ───

    "auto": ProductCategory(
        slug="auto",
        name_az="Avtomobil",
        emoji="\U0001f697",
        trigger_keywords=(
            "avtomobil", "masin", "ma\u015f\u0131n",
            "mercedes", "bmw", "audi", "toyota", "hyundai",
            "kia", "chevrolet", "ford", "nissan", "lexus",
            "tesla", "avtomobil ehtiyat",
        ),
        exclude_words=frozenset(),
    ),
    "auto_parts": ProductCategory(
        slug="auto_parts",
        name_az="Ehtiyat Hiss\u0259l\u0259ri",
        emoji="\U0001f527",
        trigger_keywords=(
            "ehtiyat hisse", "ehtiyat hiss\u0259",
            "yag filteri", "ya\u011f filteri", "hava filteri",
            "tormoz", "disk", "sveca",
            "akkumulyator", "akb",
            "tekerlek", "t\u0259k\u0259r", "shin", "\u015fin",
        ),
        exclude_words=frozenset(),
    ),
    "auto_accessory": ProductCategory(
        slug="auto_accessory",
        name_az="Avto Aksessuar",
        emoji="\U0001f698",
        trigger_keywords=(
            "avto aksessuar", "videoqeydiyyatci",
            "videoreqistrator", "naviqator", "gps",
            "avto kamera", "oturacaq uzluyu",
            "avto yuyucu", "kompressor",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Food & Grocery ───

    "food": ProductCategory(
        slug="food",
        name_az="Qida / \u018frzaq",
        emoji="\U0001f6d2",
        trigger_keywords=(
            "erzaq", "\u0259rzaq", "qida", "meyveler",
            "pendir", "makaron", "konserv",
            "sirop", "kompot",
            "protein", "whey", "vitamin",
            "qehve", "q\u0259hv\u0259",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Pets ───

    "pet": ProductCategory(
        slug="pet",
        name_az="Ev Heyvanlar\u0131",
        emoji="\U0001f43e",
        trigger_keywords=(
            "ev heyvani", "ev heyvan\u0131", "it yemi",
            "pisik yemi", "pi\u015fik yemi", "akvarium",
            "teraryum", "qus qefesi", "qu\u015f q\u0259f\u0259si",
            "it tasmas\u0131", "pet", "it evi",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Books & Stationery ───

    "books": ProductCategory(
        slug="books",
        name_az="Kitab",
        emoji="\U0001f4da",
        trigger_keywords=(
            "kitab", "roman", "derslik",
            "luget", "l\u00fc\u011f\u0259t", "enselopediya",
            "kindle", "e-reader",
        ),
        exclude_words=frozenset(),
    ),
    "stationery": ProductCategory(
        slug="stationery",
        name_az="D\u0259ft\u0259rxana",
        emoji="\u270f\ufe0f",
        trigger_keywords=(
            "defter", "d\u0259ft\u0259r", "qelem", "q\u0259l\u0259m",
            "marker", "boya", "rucka", "ru\u00e7ka",
            "kalkulyator", "defterhana", "d\u0259ft\u0259rxana",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Health & Medical ───

    "health": ProductCategory(
        slug="health",
        name_az="Sa\u011flaml\u0131q",
        emoji="\u2695\ufe0f",
        trigger_keywords=(
            "tonometr", "termometr", "tibbi", "massaj",
            "ingalyator", "nebulayzer", "ortopedik",
            "eynekler", "linza", "linzalar",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Home & Garden ───

    "home_decor": ProductCategory(
        slug="home_decor",
        name_az="Ev Dekoru",
        emoji="\U0001f3a8",
        trigger_keywords=(
            "dekor", "perde", "p\u0259rd\u0259", "xali", "xal\u0131",
            "xalca", "xal\u00e7a", "gul", "g\u00fcl", "vazo",
            "saat", "divar saati", "g\u00fczg\u00fc", "guzgu",
            "yastiq", "yast\u0131q", "yorgan",
        ),
        exclude_words=frozenset(),
    ),
    "garden": ProductCategory(
        slug="garden",
        name_az="Ba\u011f / H\u0259y\u0259t",
        emoji="\U0001f331",
        trigger_keywords=(
            "bag aleti", "ba\u011f al\u0259ti", "lawn mower",
            "ot bicen", "ot bi\u00e7\u0259n", "bag hortumu",
            "sulama", "gilabi", "qazon",
        ),
        exclude_words=frozenset(),
    ),
    "tools": ProductCategory(
        slug="tools",
        name_az="Al\u0259tl\u0259r",
        emoji="\U0001f6e0\ufe0f",
        trigger_keywords=(
            "drel", "qaynaq", "bolgarka", "suvag",
            "alet desti", "al\u0259t d\u0259sti", "tornavida",
            "acqic", "a\u00e7q\u0131c", "olcu", "\u00f6l\u00e7\u00fc",
            "bosch", "makita", "dewalt", "stanley",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Musical Instruments ───

    "music": ProductCategory(
        slug="music",
        name_az="Musiqi Al\u0259tl\u0259ri",
        emoji="\U0001f3b5",
        trigger_keywords=(
            "gitara", "piano", "royal", "sintezator",
            "beben", "b\u0259b\u0259n", "skripka", "fleyta",
            "ukulele", "midi", "mikrofon", "microphone",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Gaming ───

    "gaming_accessory": ProductCategory(
        slug="gaming_accessory",
        name_az="Oyun Aksesuarlar\u0131",
        emoji="\U0001f579\ufe0f",
        trigger_keywords=(
            "joystick", "gamepad", "controller",
            "gaming mouse", "gaming keyboard",
            "gaming qulaqliq", "steering wheel",
            "vr", "oculus", "meta quest",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Smart Home & Security ───

    "smart_home": ProductCategory(
        slug="smart_home",
        name_az="A\u011f\u0131ll\u0131 Ev",
        emoji="\U0001f3e1",
        trigger_keywords=(
            "smart home", "aqilli ev", "a\u011f\u0131ll\u0131 ev",
            "aqilli lampa", "smart plug", "robot tozsoran",
            "nezearet kamerasi", "n\u0259zar\u0259t kameras\u0131",
            "domofon", "siqnalizasiya", "smart lock",
        ),
        exclude_words=frozenset(),
    ),

    # ─── Office ───

    "office": ProductCategory(
        slug="office",
        name_az="Ofis Avadanl\u0131\u011f\u0131",
        emoji="\U0001f4bc",
        trigger_keywords=(
            "ofis", "proyektor", "projector",
            "seyf", "laminasiya", "skaner", "kartric",
        ),
        exclude_words=ACCESSORY_WORDS,
    ),

    # ─── Fallback / Meta ───

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


def _keyword_matches(keyword: str, query_lower: str, query_tokens: set[str]) -> bool:
    """Check if a trigger keyword matches in the query.

    Short keywords (<=3 chars) use exact token matching to avoid
    false positives (e.g. "tv" inside "aktivl\u0259\u015fdir", "un" inside "samsung").
    Longer keywords use substring matching to handle morphological suffixes.
    """
    if len(keyword) <= 3:
        return keyword in query_tokens
    return keyword in query_lower


def detect_categories(query: str) -> list[ProductCategory]:
    """Detect matching product categories from a search query.

    Returns a list of ProductCategory items:
    - All detected categories (sorted by keyword specificity)
    - ``accessory`` (always)
    - ``all`` (always)
    - Falls back to ``main_product`` + accessory + all when nothing detected.

    Longer / more-specific trigger keywords are checked first so that
    e.g. "galaxy tab" matches *tablet* before "galaxy" could match *phone*.
    """
    import re

    query_lower = query.lower()
    query_tokens = set(re.split(r'[\s\-/,.()\[\]]+', query_lower))

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
        if _keyword_matches(kw, query_lower, query_tokens):
            detected.append(cat)
            seen_slugs.add(cat.slug)

    # Fallback when nothing detected
    if not detected:
        detected.append(CATEGORIES["main_product"])

    # Always append accessory and all
    detected.append(CATEGORIES["accessory"])
    detected.append(CATEGORIES["all"])

    return detected
