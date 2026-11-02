"""One borrowing event."""


class Loan:
    MAX_RENEWALS = 2  # R6

    # Class attribute: ONE counter shared by every loan, because a new loan's number
    # depends on all the loans that exist, not on any single loan.
    _next_number = 1

    def __init__(self, loan_id, member_id, isbn, issue_date, due_date, return_date=None, renewals=0):
        if due_date < issue_date:
            raise ValueError("Due date cannot be before the issue date.")
        # Instance attributes: each loan has its own dates and renewal count.
        self.loan_id = loan_id
        self.member_id = member_id
        self.isbn = isbn
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date
        self.renewals = renewals

    @classmethod
    def reset_counter(cls, value):
        cls._next_number = value

    @classmethod
    def new_id(cls):
        loan_id = f"L{cls._next_number:03d}"
        cls._next_number += 1
        return loan_id

    @property
    def is_open(self):
        return self.return_date is None

    def days_late(self, on_date):
        """R10: returning on the due date is not late; the first late day is the day after."""
        return max(0, (on_date - self.due_date).days)

    def is_overdue(self, today):
        return self.is_open and today > self.due_date

    def fine(self, on_date, rate, price):
        """R5: days late x daily rate, never more than the item's price."""
        return min(self.days_late(on_date) * rate, price)

    def __str__(self):
        state = "open" if self.is_open else f"returned {self.return_date}"
        return f"{self.loan_id}: {self.member_id} / {self.isbn} due {self.due_date} ({state})"

    def __repr__(self):
        return f"Loan({self.loan_id!r}, {self.member_id!r}, {self.isbn!r})"
