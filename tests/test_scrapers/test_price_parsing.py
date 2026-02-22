from decimal import Decimal
import pytest

from app.backend.scrapers.base import BaseScraper


class TestPriceParsing:
    def test_simple_integer(self):
        assert BaseScraper._parse_price("1299") == Decimal("1299.00")

    def test_with_currency_symbol(self):
        assert BaseScraper._parse_price("1 299 ₼") == Decimal("1299.00")

    def test_with_azn_suffix(self):
        assert BaseScraper._parse_price("1 299.99 AZN") == Decimal("1299.99")

    def test_comma_decimal(self):
        assert BaseScraper._parse_price("1299,99") == Decimal("1299.99")

    def test_dot_thousands_comma_decimal(self):
        assert BaseScraper._parse_price("1.299,00 ₼") == Decimal("1299.00")

    def test_comma_thousands_dot_decimal(self):
        assert BaseScraper._parse_price("1,299.00") == Decimal("1299.00")

    def test_space_thousands(self):
        assert BaseScraper._parse_price("1 299 ₼") == Decimal("1299.00")

    def test_space_thousands_with_decimal(self):
        assert BaseScraper._parse_price("1 299,99 ₼") == Decimal("1299.99")

    def test_simple_decimal(self):
        assert BaseScraper._parse_price("1299.99") == Decimal("1299.99")

    def test_large_price(self):
        assert BaseScraper._parse_price("12 999 ₼") == Decimal("12999.00")

    def test_small_price(self):
        assert BaseScraper._parse_price("99 ₼") == Decimal("99.00")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            BaseScraper._parse_price("")

    def test_no_digits_raises(self):
        with pytest.raises(ValueError):
            BaseScraper._parse_price("₼₼₼")

    def test_whitespace_handling(self):
        assert BaseScraper._parse_price("  1299  ₼  ") == Decimal("1299.00")

    def test_dot_thousands_no_decimal(self):
        assert BaseScraper._parse_price("1.299 ₼") == Decimal("1299.00")
