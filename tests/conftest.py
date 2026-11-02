import os
from datetime import date

import pytest

from library import Library

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
TODAY = date(2026, 10, 12)

WINGS, ALCHEMIST, CLEAN, PYTHON, SAPIENS, ENCYC, MAGAZINE = (
    "9780000000011", "9780000000028", "9780000000035", "9780000000042",
    "9780000000059", "9780000000066", "9780000000073")


@pytest.fixture
def lib():
    """A fresh library loaded from the starter data. Every test gets its own copy."""
    library = Library()
    library.load_data(DATA)
    return library


@pytest.fixture
def today():
    return TODAY
