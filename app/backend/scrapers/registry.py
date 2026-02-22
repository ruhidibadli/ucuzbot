import importlib
import pkgutil
from pathlib import Path

from app.backend.scrapers.base import BaseScraper


class ScraperRegistry:
    def __init__(self):
        self._scrapers: dict[str, type[BaseScraper]] = {}
        self._discovered = False

    def register(self, scraper_class: type[BaseScraper]) -> type[BaseScraper]:
        self._scrapers[scraper_class.store_slug] = scraper_class
        return scraper_class

    def get(self, store_slug: str) -> type[BaseScraper] | None:
        self._ensure_discovered()
        return self._scrapers.get(store_slug)

    def get_all(self) -> dict[str, type[BaseScraper]]:
        self._ensure_discovered()
        return dict(self._scrapers)

    def create_instance(self, store_slug: str) -> BaseScraper | None:
        cls = self.get(store_slug)
        if cls:
            return cls()
        return None

    def _ensure_discovered(self) -> None:
        if not self._discovered:
            self._discover()
            self._discovered = True

    def _discover(self) -> None:
        package_path = Path(__file__).parent
        for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
            if module_name in ("base", "registry", "__init__"):
                continue
            importlib.import_module(f"app.backend.scrapers.{module_name}")


scraper_registry = ScraperRegistry()
