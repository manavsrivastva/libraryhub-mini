"""Writes the hand-in files schema.sql, seed.sql and queries.sql from the Python sources.
The program never READS them; this tool only WRITES them.   python export_sql.py"""
import os
import textwrap

from build_db import HERE, build_db
from sql_queries import QUERIES
from sql_schema import SCHEMA


def write(name, text):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", name)


def queries_text():
    out = ["-- LibraryHub Mini: the 12-query pack.",
           "-- Named parameter :today = '2026-10-12' is supplied by run_queries.py (never date('now'):",
           "-- the samples need a fixed date).", ""]
    for qid, question, notes, sql in QUERIES:
        out.append(f"-- {qid}: {question}")
        out += [f"-- {line}" for line in textwrap.wrap(notes, 105)]
        out.append(sql + ";")
        out.append("")
    return "\n".join(out)


def seed_text():
    """The INSERT statements of a freshly seeded database, produced by SQLite's own dump facility."""
    conn = build_db()
    inserts = [line for line in conn.iterdump()
               if line.startswith("INSERT INTO") and "sqlite_sequence" not in line]
    return "-- Seed data: the starter CSVs as INSERT statements (run schema.sql first).\n" + \
           "BEGIN TRANSACTION;\n" + "\n".join(inserts) + "\nCOMMIT;\n"


if __name__ == "__main__":
    write("schema.sql", SCHEMA)
    write("seed.sql", seed_text())
    write("queries.sql", queries_text())
