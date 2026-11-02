"""3.6: 100,000 loans, find the 2 slowest of the 12 queries, EXPLAIN before/after an index.
    python index_experiment.py          (about a minute)       Writes index_report.md
"""
import os
import random
import sys
import time
from datetime import date, timedelta

from build_db import HERE, build_db
from run_queries import load_queries

TODAY = "2026-10-12"
DB = os.path.join(HERE, "perf_test.db")

# One candidate index per query: the one that targets how that query touches `loans`.
CANDIDATES = {
    "Q2":  "CREATE INDEX idx_loans_open_due ON loans (due_date) WHERE return_date IS NULL",
    "Q3":  "CREATE INDEX idx_loans_open_due ON loans (due_date) WHERE return_date IS NULL",
    "Q4":  "CREATE INDEX idx_loans_isbn ON loans (isbn)",
    "Q5":  "CREATE INDEX idx_loans_isbn ON loans (isbn)",
    "Q6":  "CREATE INDEX idx_loans_member_issue ON loans (member_id, issue_date)",
    "Q7":  "CREATE INDEX idx_loans_member ON loans (member_id)",
    "Q9":  "CREATE INDEX idx_loans_member_isbn ON loans (member_id, isbn)",
    "Q10": "CREATE INDEX idx_loans_isbn_dates ON loans (isbn, issue_date, return_date)",
    "Q11": "CREATE INDEX idx_loans_open_isbn ON loans (isbn) WHERE return_date IS NULL",
    "Q12": "CREATE INDEX idx_loans_member_isbn ON loans (member_id, isbn)",
}


def generate(conn, n_loans=100_000, n_items=10_000, n_members=5_000, seed=1):
    rnd = random.Random(seed)
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("DELETE FROM fines"); conn.execute("DELETE FROM loans")
    conn.execute("DELETE FROM item_authors"); conn.execute("DELETE FROM items")
    conn.execute("DELETE FROM members WHERE member_id LIKE 'G%'")
    conn.executemany("INSERT INTO items VALUES (?, ?, ?, 'Book', ?, ?, 3)",
                     [(f"978{i + 1000000:010d}", f"Title {i}", rnd.randint(1, 8), rnd.randint(100, 800),
                       rnd.randint(100, 900)) for i in range(n_items)])
    types = ["Student", "Regular", "Premium"]
    conn.executemany("INSERT INTO members VALUES (?, ?, ?, ?)",
                     [(f"G{i:05d}", f"Member {i}", f"g{i}@example.com", types[i % 3]) for i in range(n_members)])
    loans, fines, open_pairs = [], [], set()
    for k in range(n_loans):
        member, isbn = f"G{rnd.randrange(n_members):05d}", f"978{rnd.randrange(n_items) + 1000000:010d}"
        issue = date(2024, 10, 12) + timedelta(days=rnd.randrange(730))
        due = issue + timedelta(days=14)
        is_open = rnd.random() < 0.05 and (member, isbn) not in open_pairs
        if is_open:
            open_pairs.add((member, isbn))
            returned = None
        else:
            returned = issue + timedelta(days=rnd.randint(3, 40))
            late = (returned - due).days
            if late > 0:
                fines.append((f"X{k:06d}", min(late * 2, 100), rnd.randint(0, 1)))
        loans.append((f"X{k:06d}", member, isbn, issue.isoformat(), due.isoformat(),
                      returned.isoformat() if returned else None))
    conn.executemany("INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date, return_date) "
                     "VALUES (?, ?, ?, ?, ?, ?)", loans)
    conn.executemany("INSERT INTO fines VALUES (?, ?, ?)", fines)
    conn.commit()
    conn.execute("ANALYZE")


def time_query(conn, sql):
    start = time.perf_counter()
    conn.execute(sql, {"today": TODAY}).fetchall()
    return (time.perf_counter() - start) * 1000


def plan(conn, sql):
    return [row[3] for row in conn.execute("EXPLAIN QUERY PLAN " + sql, {"today": TODAY})]


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if os.path.exists(DB):
        os.remove(DB)
    conn = build_db(DB)
    print("Generating 100,000 loans ...")
    generate(conn)
    out = ["# Index report (100,000 loans)", ""]
    queries = {qid: (q, sql) for qid, q, sql in load_queries()}
    times = {qid: time_query(conn, sql) for qid, (_, sql) in queries.items()}
    out += ["## All 12 queries, no extra indexes (ms)", "", "| Query | ms |", "|---|---|"]
    out += [f"| {qid} | {t:.1f} |" for qid, t in times.items()]
    slowest = [q for q, _ in sorted(times.items(), key=lambda kv: -kv[1]) if q in CANDIDATES][:2]
    before_plans = {qid: plan(conn, queries[qid][1]) for qid in slowest}   # BEFORE any index exists
    for qid in slowest:
        question, sql = queries[qid]
        before_ms, before_plan = times[qid], before_plans[qid]
        index_sql = CANDIDATES[qid]
        conn.execute(index_sql)
        conn.execute("ANALYZE")
        after_ms, after_plan = time_query(conn, sql), plan(conn, sql)
        conn.execute(f"DROP INDEX {index_sql.split()[2]}")       # keep the next experiment independent
        out += ["", f"## {qid}: {question}", "", f"Index: `{index_sql}`", "",
                f"- before: {before_ms:.1f} ms", "  - plan: " + " | ".join(before_plan),
                f"- after:  {after_ms:.1f} ms", "  - plan: " + " | ".join(after_plan),
                f"- speed-up: x{before_ms / max(after_ms, 0.001):.1f}"]
    out += ["", "## An index I decided NOT to create", "",
            "`CREATE INDEX idx_fines_paid ON fines (paid)`: `paid` has only two values, so an index on it",
            "would point at half the table either way; the planner would ignore it, while every insert and",
            "update pays to maintain it. (Write your own reason if you choose a different example.)"]
    text = "\n".join(out)
    print(text)
    with open(os.path.join(HERE, "index_report.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    conn.close()
    os.remove(DB)
