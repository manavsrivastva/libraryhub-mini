"""One connection + a transaction context manager."""
import sqlite3
from contextlib import contextmanager

from members import MEMBER_TYPES
from sql_schema import SCHEMA


class Database:
    def __init__(self, path=":memory:"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.isolation_level = None          # we issue BEGIN / COMMIT / ROLLBACK ourselves
        self.conn.execute("PRAGMA foreign_keys = ON")   # SQLite ignores foreign keys unless this is set
        self._depth = 0                           # lets transactions nest (inner ones join the outer one)
        self._create_schema_if_needed()

    def _create_schema_if_needed(self):
        found = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'items'").fetchone()
        if found:
            return
        self.conn.executescript(SCHEMA)
        self.conn.execute("PRAGMA foreign_keys = ON")
        with self.transaction():
            rows = []
            for cls in MEMBER_TYPES.values():     # the Rulebook table, taken from the member classes
                m = cls("TMP", "tmp", "t@t")
                rows.append((cls.membership_type, m.max_items(), m.loan_days(), m.fine_per_day()))
            self.conn.executemany("INSERT INTO membership_types VALUES (?, ?, ?, ?)", rows)

    def execute(self, sql, params=()):
        return self.conn.execute(sql, params)

    def one(self, sql, params=()):
        """First column of the first row (or None)."""
        row = self.conn.execute(sql, params).fetchone()
        return row[0] if row else None

    @contextmanager
    def transaction(self):
        """All statements inside succeed together or not at all.
        BEGIN IMMEDIATE takes the write lock FIRST, so two requests cannot both see the last copy free."""
        if self._depth == 0:
            self.conn.execute("BEGIN IMMEDIATE")
        self._depth += 1
        try:
            yield self
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                self.conn.execute("ROLLBACK")
            raise
        else:
            self._depth -= 1
            if self._depth == 0:
                self.conn.execute("COMMIT")

    def close(self):
        self.conn.close()
