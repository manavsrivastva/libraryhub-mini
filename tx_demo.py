"""3.6: borrow as ONE transaction, then break it on purpose.   python tx_demo.py"""
import sqlite3
import sys

from build_db import build_db


def borrow_tx(conn, member_id, isbn, today, break_audit=False):
    """All-or-nothing: check availability, insert the loan, insert the audit row.
    BEGIN IMMEDIATE takes the write lock FIRST, so two borrowers cannot both see the last copy as free."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        free = conn.execute(
            "SELECT i.total_copies - COUNT(l.loan_id) FROM items i "
            "LEFT JOIN loans l ON l.isbn = i.isbn AND l.return_date IS NULL "
            "WHERE i.isbn = ? GROUP BY i.isbn", (isbn,)).fetchone()
        if free is None or free[0] <= 0:
            raise LookupError("no copy available")
        conn.execute(
            "INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date) "
            "SELECT 'L' || printf('%03d', COALESCE(MAX(CAST(substr(loan_id, 2) AS INTEGER)), 0) + 1), "
            "       ?, ?, ?, date(?, '+' || mt.loan_days || ' days') "
            "FROM loans, members m JOIN membership_types mt ON mt.type_name = m.membership_type "
            "WHERE m.member_id = ?", (member_id, isbn, today, today, member_id))
        conn.execute("INSERT INTO audit_log (logged_at, action, member_id, isbn) VALUES (?, ?, ?, ?)",
                     (today, None if break_audit else "borrow", member_id, isbn))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")      # undo EVERY statement of this transaction
        raise


def count(conn, sql):
    return conn.execute(sql).fetchone()[0]


if __name__ == "__main__":
    conn = build_db()
    conn.isolation_level = None       # we write BEGIN / COMMIT / ROLLBACK ourselves
    loans = "SELECT COUNT(*) FROM loans WHERE loan_id = 'L011'"
    print("-- before")
    print(f"loans with L011: {count(conn, loans)}   audit rows: {count(conn, 'SELECT COUNT(*) FROM audit_log')}")
    print("\n-- attempt 1: audit insert violates NOT NULL on purpose")
    try:
        borrow_tx(conn, "M001", "9780000000011", "2026-10-12", break_audit=True)
    except sqlite3.IntegrityError as err:
        print(f"ERROR: {err}  -> ROLLBACK")
    print(f"loans with L011: {count(conn, loans)}   audit rows: {count(conn, 'SELECT COUNT(*) FROM audit_log')}")
    print("\n-- attempt 2: correct statements")
    borrow_tx(conn, "M001", "9780000000011", "2026-10-12")
    print(f"loans with L011: {count(conn, loans)}   audit rows: {count(conn, 'SELECT COUNT(*) FROM audit_log')}")
    print("due date:", conn.execute("SELECT due_date FROM loans WHERE loan_id = 'L011'").fetchone()[0])
