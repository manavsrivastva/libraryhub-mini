"""Phase 3 Part A: schema, seed, the 12 queries, constraints, transactions, injection."""
import sqlite3

import pytest

from build_db import build_db, counts
from injection_unsafe_demo import search_safe, search_unsafe
from run_queries import run_all
from tx_demo import borrow_tx, count


def fresh():
    return build_db()          # a brand-new in-memory database for every test


# ---------------------------------------------------------------- loading
def test_counts_after_loading():
    assert counts(fresh()) == {"items": 7, "authors": 7, "members": 5, "loans": 10,
                               "fines": 4, "categories": 8, "open_loans": 3}


# ---------------------------------------------------------------- the 12 queries
EXPECTED = {
    "Q1": [("Wings of Fire", "A.P.J. Abdul Kalam"), ("Wings of Fire", "Arun Tiwari")],
    "Q2": [("L001", "Rahul Mehta", "The Alchemist"), ("L002", "Karthik N", "Python Crash Course"),
           ("L003", "Sneha Iyer", "Sapiens")],
    "Q3": [("Rahul Mehta", "The Alchemist", "2026-09-22", 20),
           ("Karthik N", "Python Crash Course", "2026-10-05", 7)],
    "Q4": [("Python Crash Course", 3), ("Wings of Fire", 3), ("Clean Code", 1)],
    "Q5": [("Encyclopaedia of Science",)],
    "Q6": [("Divya Rao",)],
    "Q7": [("Regular", "2026-06", 40), ("Student", "2026-08", 50), ("Student", "2026-09", 80)],
    "Q8": [("Paid", 50), ("Pending", 120)],
    "Q9": [("Karthik N", 3), ("Rahul Mehta", 3)],
    "Q10": [("Magazines", 67.0), ("Software Engineering", 28.0), ("Biography", 25.7)],
    "Q11": [("Wings of Fire", 2), ("The Alchemist", 0), ("Clean Code", 1), ("Python Crash Course", 1),
            ("Sapiens", 0), ("Encyclopaedia of Science", 1), ("India Today (Oct 2026)", 3)],
    "Q12": [("Python Crash Course", "Wings of Fire", 3)],
}


@pytest.mark.parametrize("qid", sorted(EXPECTED, key=lambda q: int(q[1:])))
def test_query_matches_expected_output(qid):
    results = {r[0]: r[3] for r in run_all(fresh())}
    assert results[qid] == EXPECTED[qid]


def test_there_are_exactly_12_queries():
    assert len(run_all(fresh())) == 12


# ---------------------------------------------------------------- constraints
def test_foreign_key_rejects_unknown_member():
    with pytest.raises(sqlite3.IntegrityError):
        fresh().execute("INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date) "
                        "VALUES ('L900', 'M999', '9780000000011', '2026-10-12', '2026-10-26')")


def test_restrict_blocks_deleting_a_member_with_loans():
    with pytest.raises(sqlite3.IntegrityError):
        fresh().execute("DELETE FROM members WHERE member_id = 'M002'")


def test_member_without_loans_can_be_deleted():
    conn = fresh()
    conn.execute("DELETE FROM members WHERE member_id = 'M005'")
    assert counts(conn)["members"] == 4


def test_r8_partial_unique_index_one_open_loan_per_title():
    conn = fresh()
    with pytest.raises(sqlite3.IntegrityError):      # M002 already has L001 open for The Alchemist
        conn.execute("INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date) "
                     "VALUES ('L900', 'M002', '9780000000028', '2026-10-12', '2026-11-02')")
    # but a title already RETURNED may be borrowed again (history can repeat)
    conn.execute("INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date) "
                 "VALUES ('L901', 'M001', '9780000000011', '2026-10-12', '2026-10-26')")


@pytest.mark.parametrize("sql", [
    "INSERT INTO items VALUES ('123', 'T', 1, 'Book', 10, 10, 1)",                    # R9: not 13 digits
    "INSERT INTO items VALUES ('97800000000AB', 'T', 1, 'Book', 10, 10, 1)",          # R9: letters
    "INSERT INTO items VALUES ('9780000000011', 'Dup', 1, 'Book', 10, 10, 1)",        # R9: unique
    "INSERT INTO items VALUES ('9780000000999', 'T', 1, 'Book', 10, 10, -1)",         # copies >= 0
    "INSERT INTO items VALUES ('9780000000999', '  ', 1, 'Book', 10, 10, 1)",         # blank title
    "INSERT INTO members VALUES ('M900', 'X', 'asha@example.com', 'Student')",        # email unique
    "INSERT INTO members VALUES ('M900', 'X', 'no-at-sign', 'Student')",              # email needs @
    "INSERT INTO fines VALUES ('L004', -5, 0)",                                       # fine >= 0
    "INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date) "
    "VALUES ('L900', 'M001', '9780000000066', '2026-10-12', '2026-10-01')",           # due before issue
])
def test_check_unique_and_not_null_constraints(sql):
    with pytest.raises(sqlite3.IntegrityError):
        fresh().execute(sql)


# ---------------------------------------------------------------- transactions
def make_conn():
    conn = fresh()
    conn.isolation_level = None
    return conn


def test_failed_transaction_leaves_no_trace():
    conn = make_conn()
    with pytest.raises(sqlite3.IntegrityError):
        borrow_tx(conn, "M001", "9780000000011", "2026-10-12", break_audit=True)
    assert count(conn, "SELECT COUNT(*) FROM loans WHERE loan_id = 'L011'") == 0
    assert count(conn, "SELECT COUNT(*) FROM audit_log") == 0


def test_successful_transaction_commits_both_rows():
    conn = make_conn()
    borrow_tx(conn, "M001", "9780000000011", "2026-10-12")
    assert count(conn, "SELECT COUNT(*) FROM loans WHERE loan_id = 'L011'") == 1
    assert count(conn, "SELECT COUNT(*) FROM audit_log") == 1
    assert conn.execute("SELECT due_date FROM loans WHERE loan_id = 'L011'").fetchone()[0] == "2026-10-26"


def test_transaction_refuses_when_no_copy_is_free():
    conn = make_conn()
    with pytest.raises(LookupError):
        borrow_tx(conn, "M003", "9780000000028", "2026-10-12")      # The Alchemist: 0 of 1
    assert count(conn, "SELECT COUNT(*) FROM loans") == 10


# ---------------------------------------------------------------- injection
def test_sql_injection_experiment():
    conn = fresh()
    attack = "' OR '1'='1"
    assert len(search_unsafe(conn, "Python")) == 1
    assert len(search_unsafe(conn, attack)) == 7        # every item leaked
    assert len(search_safe(conn, attack)) == 0
    assert len(search_safe(conn, "Python")) == 1


# ---------------------------------------------------------------- the hand-in .sql files
def read_or_none(name):
    import os
    from build_db import HERE
    try:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return f.read()
    except (PermissionError, FileNotFoundError):
        return None        # a locked-down laptop may refuse to read .sql files: the program never needs them


def test_handin_sql_files_match_the_python_sources():
    from sql_schema import SCHEMA
    text = read_or_none("schema.sql")
    if text is not None:
        assert text == SCHEMA, "schema.sql is out of date: run python export_sql.py"


def test_handin_schema_and_seed_files_really_load_in_sqlite():
    schema, seed = read_or_none("schema.sql"), read_or_none("seed.sql")
    if schema is None or seed is None:
        return
    conn = sqlite3.connect(":memory:")
    conn.executescript(schema)
    conn.executescript(seed)
    assert counts(conn) == {"items": 7, "authors": 7, "members": 5, "loans": 10,
                            "fines": 4, "categories": 8, "open_loans": 3}
