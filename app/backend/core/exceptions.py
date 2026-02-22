class UcuzBotError(Exception):
    pass


class ScraperError(UcuzBotError):
    def __init__(self, store_slug: str, message: str):
        self.store_slug = store_slug
        super().__init__(f"[{store_slug}] {message}")


class AlertLimitReached(UcuzBotError):
    def __init__(self, max_alerts: int):
        self.max_alerts = max_alerts
        super().__init__(f"Alert limit reached: {max_alerts}")


class StoreNotFound(UcuzBotError):
    pass


class AlertNotFound(UcuzBotError):
    pass
