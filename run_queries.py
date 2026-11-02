"""Run the 12 queries.   python run_queries.py [YYYY-MM-DD]"""
import sys

from build_db import build_db
from sql_queries import QUERIES


def load_queries():
    """(id, business question, sql) for each query."""
    return [(qid, question, sql) for qid, question, _notes, sql in QUERIES]


def run_all(conn, today="2026-10-12"):
    results = []
    for qid, question, sql in load_queries():
        cur = conn.execute(sql, {"today": today})
        results.append((qid, question, [c[0] for c in cur.description], cur.fetchall()))
    return results


def show(results):
    for qid, question, cols, rows in results:
        print(f"{qid}  {question}")
        table = [cols] + [[str(v) for v in row] for row in rows]
        widths = [max(len(str(r[i])) for r in table) for i in range(len(cols))]
        for row in table:
            print(" | ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip())
        print()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    show(run_all(build_db(), sys.argv[1] if len(sys.argv) > 1 else "2026-10-12"))
