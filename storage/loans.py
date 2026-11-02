"""Loans and fines."""
from datetime import date

from loans import Loan

COLUMNS = "loan_id, member_id, isbn, issue_date, due_date, return_date, renewals"


def _to_date(text):
    return date.fromisoformat(text) if text else None


def _build(row):
    loan_id, member_id, isbn, issued, due, returned, renewals = row
    return Loan(loan_id, member_id, isbn, _to_date(issued), _to_date(due), _to_date(returned), renewals)


class LoanRepository:
    def __init__(self, db):
        self.db = db

    # ---- loans -----------------------------------------------------------------
    def next_id(self):
        """MAX + 1 inside the borrow transaction, so an undone borrow gives its number back."""
        highest = self.db.one("SELECT MAX(CAST(substr(loan_id, 2) AS INTEGER)) FROM loans") or 0
        return f"L{highest + 1:03d}"

    def add(self, loan):
        self.db.execute("INSERT INTO loans (" + COLUMNS + ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (loan.loan_id, loan.member_id, loan.isbn, loan.issue_date.isoformat(),
                         loan.due_date.isoformat(),
                         loan.return_date.isoformat() if loan.return_date else None, loan.renewals))

    def get(self, loan_id):
        row = self.db.execute("SELECT " + COLUMNS + " FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
        return _build(row) if row else None

    def all(self):
        return [_build(r) for r in self.db.execute("SELECT " + COLUMNS + " FROM loans ORDER BY rowid")]

    def open_for_member(self, member_id):
        return [_build(r) for r in self.db.execute(
            "SELECT " + COLUMNS + " FROM loans WHERE member_id = ? AND return_date IS NULL ORDER BY rowid",
            (member_id,))]

    def history_for_member(self, member_id):
        return [_build(r) for r in self.db.execute(
            "SELECT " + COLUMNS + " FROM loans WHERE member_id = ? ORDER BY issue_date, loan_id",
            (member_id,))]

    def count_open(self, member_id):
        return self.db.one("SELECT COUNT(*) FROM loans WHERE member_id = ? AND return_date IS NULL",
                           (member_id,))

    def has_open_loan(self, member_id, isbn):
        return self.db.one("SELECT 1 FROM loans WHERE member_id = ? AND isbn = ? AND return_date IS NULL",
                           (member_id, isbn)) is not None

    def overdue(self, today):
        """Yields one overdue loan at a time straight from the cursor."""
        cur = self.db.execute("SELECT " + COLUMNS + " FROM loans WHERE return_date IS NULL AND due_date < ? "
                              "ORDER BY rowid", (today.isoformat(),))
        for row in cur:
            yield _build(row)

    def count(self):
        return self.db.one("SELECT COUNT(*) FROM loans")

    def close(self, loan_id, returned_on):
        self.db.execute("UPDATE loans SET return_date = ? WHERE loan_id = ?", (returned_on.isoformat(), loan_id))

    def reopen(self, loan_id):
        self.db.execute("UPDATE loans SET return_date = NULL WHERE loan_id = ?", (loan_id,))

    def update_renewal(self, loan_id, due_date, renewals):
        self.db.execute("UPDATE loans SET due_date = ?, renewals = ? WHERE loan_id = ?",
                        (due_date.isoformat(), renewals, loan_id))

    def delete(self, loan_id):
        self.db.execute("DELETE FROM loans WHERE loan_id = ?", (loan_id,))

    # ---- fines -----------------------------------------------------------------
    def add_fine(self, loan_id, amount, paid=False):
        self.db.execute("INSERT INTO fines VALUES (?, ?, ?)", (loan_id, amount, 1 if paid else 0))

    def delete_fine(self, loan_id):
        self.db.execute("DELETE FROM fines WHERE loan_id = ?", (loan_id,))

    def all_fines(self):
        return [{"loan_id": loan_id, "amount": amount, "paid": bool(paid)}
                for loan_id, amount, paid in self.db.execute(
                    "SELECT loan_id, amount, paid FROM fines ORDER BY rowid")]

    def fine_count(self):
        return self.db.one("SELECT COUNT(*) FROM fines")

    def unpaid_total(self, member_id):
        return self.db.one("SELECT COALESCE(SUM(f.amount), 0) FROM fines f JOIN loans l ON l.loan_id = f.loan_id "
                           "WHERE l.member_id = ? AND f.paid = 0", (member_id,))

    def members_with_unpaid(self):
        return self.db.execute("SELECT l.member_id, SUM(f.amount) FROM fines f JOIN loans l ON l.loan_id = f.loan_id "
                               "WHERE f.paid = 0 GROUP BY l.member_id").fetchall()
