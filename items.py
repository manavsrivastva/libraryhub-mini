"""Catalogue items. LibraryItem is abstract: each subclass must answer three questions."""
from abc import ABC, abstractmethod

from errors import InvalidISBNError


class LibraryItem(ABC):
    type_name = "Item"  # class attribute: the same for every instance of a subclass

    def __init__(self, isbn, title, authors, category, parent_category, pages, price, total_copies):
        self.isbn = isbn                  # each assignment goes through a validating setter
        self.title = title
        self.authors = list(authors)
        self.category = category
        self.parent_category = parent_category or None
        self.pages = int(pages)
        self.price = int(price)
        self.total_copies = total_copies
        # Instance attribute: every item has its OWN number of free copies.
        self.available = self.total_copies

    # ---- validated properties -------------------------------------------------
    @property
    def isbn(self):
        return self._isbn

    @isbn.setter
    def isbn(self, value):
        value = str(value).strip()
        if len(value) != 13 or not value.isdigit():  # R9
            raise InvalidISBNError("ISBN must be exactly 13 digits.")
        self._isbn = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not str(value).strip():
            raise ValueError("Title cannot be blank.")
        self._title = str(value).strip()

    @property
    def total_copies(self):
        return self._total_copies

    @total_copies.setter
    def total_copies(self, value):
        value = int(value)
        if value < 0:
            raise ValueError("Copies cannot be negative.")
        self._total_copies = value

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, value):
        if value < 0:
            raise ValueError("Available copies cannot be negative.")
        self._available = value

    @property
    def top_category(self):
        return self.parent_category or self.category

    # ---- what every subclass must answer ---------------------------------------
    @abstractmethod
    def is_borrowable(self): ...

    @abstractmethod
    def loan_days(self, member): ...

    @abstractmethod
    def can_renew(self): ...

    def availability_label(self, free):
        return f"{free} of {self.total_copies}"

    def __str__(self):
        return f"{self.title} ({self.isbn})"

    def __repr__(self):
        return f"{type(self).__name__}(isbn={self.isbn!r}, title={self.title!r})"


class Book(LibraryItem):
    type_name = "Book"

    def is_borrowable(self):
        return True

    def loan_days(self, member):
        return member.loan_days()  # the member decides: 14 / 21 / 30

    def can_renew(self):
        return True


class Magazine(LibraryItem):
    type_name = "Magazine"

    def is_borrowable(self):
        return True

    def loan_days(self, member):
        return 7  # R2: whatever the membership

    def can_renew(self):
        return False  # R2


class ReferenceItem(LibraryItem):
    type_name = "Reference"

    def is_borrowable(self):
        return False  # R1

    def loan_days(self, member):
        return 0

    def can_renew(self):
        return False

    def availability_label(self, free):
        return "not borrowable"


ITEM_TYPES = {"Book": Book, "Magazine": Magazine, "Reference": ReferenceItem}
