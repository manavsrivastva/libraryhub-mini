"""Create the database and load the starter data.   python build_db.py [library.db]
Nothing here reads a .sql file: the schema comes from sql_schema.py and the rows from data/*.csv."""
import os
import sys

from library import Library
from storage import Database

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def build_db(path=":memory:", seed=True):
    """Returns the raw sqlite3 connection (for running queries directly)."""
    db = Database(path)
    if seed:
        Library(db).load_data(DATA)
    return db.conn


def counts(conn):
    one = lambda sql: conn.execute(sql).fetchone()[0]
    return {"items": one("SELECT COUNT(*) FROM items"), "authors": one("SELECT COUNT(*) FROM authors"),
            "members": one("SELECT COUNT(*) FROM members"), "loans": one("SELECT COUNT(*) FROM loans"),
            "fines": one("SELECT COUNT(*) FROM fines"), "categories": one("SELECT COUNT(*) FROM categories"),
            "open_loans": one("SELECT COUNT(*) FROM loans WHERE return_date IS NULL")}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "library.db")
    if os.path.exists(target):
        os.remove(target)
    conn = build_db(target)
    c = counts(conn)
    print(f"Created {target}")
    print(f"{c['items']} items, {c['authors']} authors, {c['members']} members, {c['loans']} loans, "
          f"{c['fines']} fines, {c['categories']} categories, {c['open_loans']} open loans.")
    conn.close()
