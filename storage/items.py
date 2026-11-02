"""Items, categories and authors."""
from collections import defaultdict

from items import ITEM_TYPES

# available = total copies minus copies currently out on loan (calculated, never stored: decision D13)
SELECT_ITEMS = (
    "SELECT i.isbn, i.title, c.name, p.name, i.item_type, i.pages, i.price, i.total_copies, "
    "       i.total_copies - (SELECT COUNT(*) FROM loans l WHERE l.isbn = i.isbn AND l.return_date IS NULL) "
    "FROM items i "
    "JOIN categories c ON c.category_id = i.category_id "
    "LEFT JOIN categories p ON p.category_id = c.parent_id ")


class ItemRepository:
    def __init__(self, db):
        self.db = db

    # ---- reading ---------------------------------------------------------------
    def _build(self, rows, authors):
        result = []
        for isbn, title, category, parent, item_type, pages, price, total, free in rows:
            item = ITEM_TYPES[item_type](isbn, title, authors.get(isbn, []), category, parent,
                                         pages, price, total)
            item.available = free
            result.append(item)
        return result

    def _authors(self, isbn=None):
        if isbn is None:
            cur = self.db.execute("SELECT ia.isbn, a.name FROM item_authors ia "
                                  "JOIN authors a ON a.author_id = ia.author_id ORDER BY ia.isbn, ia.position")
        else:
            cur = self.db.execute("SELECT ia.isbn, a.name FROM item_authors ia "
                                  "JOIN authors a ON a.author_id = ia.author_id "
                                  "WHERE ia.isbn = ? ORDER BY ia.position", (isbn,))
        grouped = defaultdict(list)
        for row_isbn, name in cur:
            grouped[row_isbn].append(name)
        return grouped

    def get(self, isbn):
        rows = self.db.execute(SELECT_ITEMS + "WHERE i.isbn = ?", (isbn,)).fetchall()
        return self._build(rows, self._authors(isbn))[0] if rows else None

    def all(self):
        rows = self.db.execute(SELECT_ITEMS + "ORDER BY i.rowid").fetchall()
        return self._build(rows, self._authors())

    def exists(self, isbn):
        return self.db.one("SELECT 1 FROM items WHERE isbn = ?", (isbn,)) is not None

    def count(self):
        return self.db.one("SELECT COUNT(*) FROM items")

    def search(self, text):
        """Case-insensitive substring match on title or any author. instr() treats % and _ as plain text."""
        rows = self.db.execute(
            SELECT_ITEMS + "WHERE instr(lower(i.title), ?) > 0 OR EXISTS ("
            "  SELECT 1 FROM item_authors ia JOIN authors a ON a.author_id = ia.author_id "
            "  WHERE ia.isbn = i.isbn AND instr(lower(a.name), ?) > 0) ORDER BY i.rowid",
            (text.lower(), text.lower())).fetchall()
        return self._build(rows, self._authors())

    # ---- writing ---------------------------------------------------------------
    def _category_id(self, name, parent_name):
        parent_id = self._category_id(parent_name, None) if parent_name else None
        found = self.db.one("SELECT category_id FROM categories WHERE name = ?", (name,))
        if found is not None:
            return found
        return self.db.execute("INSERT INTO categories (name, parent_id) VALUES (?, ?)",
                               (name, parent_id)).lastrowid

    def _author_id(self, name):
        found = self.db.one("SELECT author_id FROM authors WHERE name = ?", (name,))
        if found is not None:
            return found
        return self.db.execute("INSERT INTO authors (name) VALUES (?)", (name,)).lastrowid

    def add(self, item):
        with self.db.transaction():
            category_id = self._category_id(item.category, item.parent_category)
            self.db.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (item.isbn, item.title, category_id, item.type_name, item.pages,
                             item.price, item.total_copies))
            for position, name in enumerate(item.authors, 1):
                self.db.execute("INSERT INTO item_authors VALUES (?, ?, ?)",
                                (item.isbn, self._author_id(name), position))
