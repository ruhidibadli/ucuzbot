from decimal import Decimal
from unittest.mock import MagicMock

from app.backend.services.price_service import check_price_trigger


class TestAlertTrigger:
    def _make_alert(self, target_price: str) -> MagicMock:
        alert = MagicMock()
        alert.target_price = Decimal(target_price)
        return alert

    def test_triggers_when_price_below_target(self):
        alert = self._make_alert("1500.00")
        assert check_price_trigger(alert, Decimal("1450.00")) is True

    def test_triggers_when_price_equals_target(self):
        alert = self._make_alert("1500.00")
        assert check_price_trigger(alert, Decimal("1500.00")) is True

    def test_does_not_trigger_when_price_above_target(self):
        alert = self._make_alert("1500.00")
        assert check_price_trigger(alert, Decimal("1501.00")) is False

    def test_triggers_with_small_difference(self):
        alert = self._make_alert("1500.00")
        assert check_price_trigger(alert, Decimal("1499.99")) is True

    def test_does_not_trigger_with_small_difference(self):
        alert = self._make_alert("1500.00")
        assert check_price_trigger(alert, Decimal("1500.01")) is False
