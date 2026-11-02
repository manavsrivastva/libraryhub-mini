"""The Library: enforces the Rulebook and reads/writes ONLY through the storage classes.
It never reads the clock; every date-dependent method receives `today` from the caller."""
import csv
import functools
import os
from collections import defaultdict, namedtuple
from datetime import date, datetime, timedelta

from dsa.categories import build_tree
from dsa.history import BorrowHistory
from errors import (BorrowLimitExceededError, DuplicateISBNError, DuplicateLoanError,
                    InvalidISBNError, ItemNotAvailableError, ItemNotBorrowableError,
                    ItemNotFoundError, LoanNotFoundError, MemberNotFoundError,
                    RenewalNotAllowedError, UnpaidFinesError)
from items import ITEM_TYPES
from loans import Loan
from members import MEMBER_TYPES
from storage import (AuditRepository, Database, ItemRepository, LoanRepository,
                     MemberRepository, ReservationRepository)

FINE_LIMIT = 100  # R4: unpaid fines ABOVE this block borrowing

ReturnResult = namedtuple("ReturnResult", "loan days_late fine next_member")
OverdueRow = namedtuple("OverdueRow", "loan member item days fine")


def audit(action):
    """Decorator. Runs the method as ONE database transaction and, if it succeeds, writes a row to the
    audit log (time, action, member, item) inside that SAME transaction. If anything fails, everything
    (including the audit row) is rolled back. Only a committed operation becomes undoable."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self._pending_undo = None
            with self.db.transaction():
                result = func(self, *args, **kwargs)
                loan = getattr(result, "loan", result)  # ReturnResult has .loan, Loan is the loan
                self.audit_repo.add(datetime.now().isoformat(timespec="seconds"), action,
                                    loan.member_id, loan.isbn)
            if self._pending_undo is not None:       # reached only after a successful COMMIT
                self.undo_stack.append(self._pending_undo)
                self._pending_undo = None
            return result
        return wrapper
    return decorator


class Library:
    def __init__(self, db=None):
        self.db = db or Database()                    # no argument = a fresh private in-memory database
        self.item_repo = ItemRepository(self.db)
        self.member_repo = MemberRepository(self.db)
        self.loan_repo = LoanRepository(self.db)
        self.reservation_repo = ReservationRepository(self.db)
        self.audit_repo = AuditRepository(self.db)
        self.undo_stack = []                          # stack of snapshots of committed operations
        self._pending_undo = None

    # ---------------------------------------------------------------- read-only views
    @property
    def items(self):
        return {i.isbn: i for i in self.item_repo.all()}

    @property
    def members(self):
        return {m.member_id: m for m in self.member_repo.all()}

    @property
    def loans(self):
        return self.loan_repo.all()

    @property
    def fines(self):
        return self.loan_repo.all_fines()

    @property
    def audit_log(self):
        return self.audit_repo.all()

    def counts(self):
        return {"items": self.item_repo.count(), "members": self.member_repo.count(),
                "loans": self.loan_repo.count(), "fines": self.loan_repo.fine_count()}

    # ---------------------------------------------------------------- loading
    def add_item(self, item):
        if self.item_repo.exists(item.isbn):
            raise DuplicateISBNError(f"ISBN {item.isbn} already exists.")  # R9
        self.item_repo.add(item)

    def add_member(self, member):
        self.member_repo.add(member)

    def load_data(self, data_dir):
        """Fill an EMPTY database from the starter CSV files, in one transaction."""
        def rows(name):
            with open(os.path.join(data_dir, name), newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))

        with self.db.transaction():
            for r in rows("books.csv"):
                self.add_item(ITEM_TYPES[r["item_type"]](
                    r["isbn"], r["title"], r["authors"].split(";"), r["category"],
                    r["parent_category"], r["pages"], r["price"], r["total_copies"]))
            for r in rows("members.csv"):
                self.add_member(MEMBER_TYPES[r["membership_type"]](r["member_id"], r["name"], r["email"]))
            for r in rows("loans.csv"):
                ret = date.fromisoformat(r["return_date"]) if r["return_date"] else None
                self.loan_repo.add(Loan(r["loan_id"], r["member_id"], r["isbn"],
                                        date.fromisoformat(r["issue_date"]),
                                        date.fromisoformat(r["due_date"]), ret))
            for r in rows("fines.csv"):
                self.loan_repo.add_fine(r["loan_id"], int(r["amount"]), r["paid"].strip().lower() == "yes")
        return self.counts()

    # ---------------------------------------------------------------- lookups
    def get_member(self, member_id):
        member = self.member_repo.get(member_id)
        if member is None:
            raise MemberNotFoundError(f"No member with ID {member_id}.")
        return member

    def get_item(self, isbn):
        if len(isbn) != 13 or not isbn.isdigit():
            raise InvalidISBNError("ISBN must be exactly 13 digits.")
        item = self.item_repo.get(isbn)
        if item is None:
            raise ItemNotFoundError(f"No item with ISBN {isbn}.")
        return item

    def get_open_loan(self, loan_id):
        loan = self.loan_repo.get(loan_id)
        if loan is None or not loan.is_open:
            raise LoanNotFoundError(f"No open loan with ID {loan_id}.")
        return loan

    def active_loans(self, member_id):
        return self.loan_repo.open_for_member(member_id)

    def unpaid_fines(self, member_id):
        return self.loan_repo.unpaid_total(member_id)

    def waiting_names(self, isbn):
        return [self.member_repo.get(mid).name for mid in self.reservation_repo.waiting_ids(isbn)]

    def reservation_status(self, member_id, isbn):
        self.get_member(member_id)
        self.get_item(isbn)

        held_seq = self.reservation_repo.held_seq(isbn, member_id)

        if held_seq is not None:
            return {
            "status": "held",
            "position": held_seq,
        }

        if self.reservation_repo.is_queued(isbn, member_id):
            waiting_ids = self.reservation_repo.waiting_ids(isbn)
            position = waiting_ids.index(member_id) + 1

            return {
            "status": "waiting",
            "position": position,
        }

        return {
        "status": "none",
        "position": None,
    }

    def free_copies(self, isbn):
        """Copies a walk-in member could take: not out on loan and not held for the queue."""
        item = self.item_repo.get(isbn)
        return max(0, item.available - self.reservation_repo.held_count(isbn))

    # ---------------------------------------------------------------- catalogue
    def list_items(self):
        return [(i.isbn, i.title, i.type_name,
                 i.availability_label(max(0, i.available - self.reservation_repo.held_count(i.isbn))))
                for i in self.item_repo.all()]

    def search(self, text):
        q = text.strip()
        return self.item_repo.search(q) if q else []

    # ---------------------------------------------------------------- operations
    @audit("borrow")
    def borrow(self, member_id, isbn, today):
        member = self.get_member(member_id)                                   # 1
        item = self.get_item(isbn)                                            # 2
        if not item.is_borrowable():                                          # R1
            raise ItemNotBorrowableError(f"'{item.title}' is a reference item and cannot be borrowed.")
        owed = self.unpaid_fines(member_id)
        if owed > FINE_LIMIT:                                                 # R4
            raise UnpaidFinesError(f"{member.name} has unpaid fines of ₹{owed} (limit ₹{FINE_LIMIT}).")
        open_count = self.loan_repo.count_open(member_id)
        if open_count >= member.max_items():                                  # R3
            raise BorrowLimitExceededError(
                f"{member.name} already has {open_count} of {member.max_items()} items on loan.")
        if self.loan_repo.has_open_loan(member_id, isbn):                     # R8
            raise DuplicateLoanError(f"{member.name} already has a copy of '{item.title}'.")
        held_seq = self.reservation_repo.held_seq(isbn, member_id)            # availability (R7)
        if held_seq is None and self.free_copies(isbn) == 0:
            raise ItemNotAvailableError(f"No copies of '{item.title}' are available.")
        if held_seq is not None:
            self.reservation_repo.remove(isbn, member_id)                     # the held copy is now theirs
        loan = Loan(self.loan_repo.next_id(), member_id, isbn, today,
                    today + timedelta(days=item.loan_days(member)))
        self.loan_repo.add(loan)
        # A SNAPSHOT of what changed, so undo can reverse it exactly.
        self._pending_undo = {"op": "borrow", "loan_id": loan.loan_id, "held_seq": held_seq}
        return loan

    @audit("return")
    def return_item(self, loan_id, today):
        loan = self.get_open_loan(loan_id)
        member, item = self.get_member(loan.member_id), self.get_item(loan.isbn)
        late = loan.days_late(today)
        fine = loan.fine(today, member.fine_per_day(), item.price)
        self.loan_repo.close(loan.loan_id, today)
        loan.return_date = today
        if fine > 0:
            self.loan_repo.add_fine(loan.loan_id, fine)
        next_id = self.reservation_repo.hold_first(loan.isbn)  # R7: first in the queue is served first
        next_member = self.get_member(next_id) if next_id else None
        self._pending_undo = {"op": "return", "loan_id": loan.loan_id, "fine_added": fine > 0,
                              "next_id": next_id}
        return ReturnResult(loan, late, fine, next_member)

    @audit("renew")
    def renew(self, loan_id):
        loan = self.get_open_loan(loan_id)
        member, item = self.get_member(loan.member_id), self.get_item(loan.isbn)
        if not item.can_renew():                                              # R2 first
            raise RenewalNotAllowedError(f"{item.type_name}s cannot be renewed.", code="R2")
        if loan.renewals >= Loan.MAX_RENEWALS:                                # R6: limit
            raise RenewalNotAllowedError(
                f"'{item.title}' has already been renewed {Loan.MAX_RENEWALS} times.")
        if self.reservation_repo.waiting_count(loan.isbn) > 0:                # R6: someone waits
            raise RenewalNotAllowedError(
                f"'{item.title}' cannot be renewed because another member is waiting.")
        loan.due_date += timedelta(days=member.loan_days())
        loan.renewals += 1
        self.loan_repo.update_renewal(loan.loan_id, loan.due_date, loan.renewals)
        return loan

    def reserve(self, member_id, isbn):
        member = self.get_member(member_id)
        item = self.get_item(isbn)
        if not item.is_borrowable():
            raise ItemNotBorrowableError(f"'{item.title}' is a reference item and cannot be borrowed.")
        with self.db.transaction():
            if self.loan_repo.has_open_loan(member_id, isbn):
                raise DuplicateLoanError(f"{member.name} already has a copy of '{item.title}'.")
            if self.reservation_repo.is_queued(isbn, member_id):
                raise DuplicateLoanError(f"{member.name} is already on the waiting list for '{item.title}'.")
            return self.reservation_repo.join(isbn, member_id)

    def undo(self):
        """Reverse the latest committed borrow or return in ONE transaction.
        Returns a message, or None if there is nothing to undo."""
        if not self.undo_stack:
            return None
        entry = self.undo_stack[-1]
        with self.db.transaction():
            loan = self.loan_repo.get(entry["loan_id"])
            member, item = self.get_member(loan.member_id), self.get_item(loan.isbn)
            if entry["op"] == "borrow":
                self.loan_repo.delete(loan.loan_id)             # its number is free again (MAX + 1)
                if entry["held_seq"] is not None:               # give the held copy back
                    self.reservation_repo.restore_held(loan.isbn, loan.member_id, entry["held_seq"])
                message = f"Undid borrow of '{item.title}' by {member.name} (loan {loan.loan_id} removed)."
            else:
                self.loan_repo.reopen(loan.loan_id)
                if entry["fine_added"]:
                    self.loan_repo.delete_fine(loan.loan_id)
                if entry["next_id"] is not None:                # back in EXACTLY the old place in the queue
                    self.reservation_repo.unhold(loan.isbn, entry["next_id"])
                message = (f"Undid return of '{item.title}' by {member.name} "
                           f"(loan {loan.loan_id} is on loan again).")
            self.audit_repo.add(datetime.now().isoformat(timespec="seconds"),
                                f"undo-{entry['op']}", loan.member_id, loan.isbn)
        self.undo_stack.pop()                                   # only after the transaction committed
        return message

    # ---------------------------------------------------------------- reports
    def member_loans(self, member_id, today):
        member = self.get_member(member_id)
        active = [(l, self.get_item(l.isbn), l.days_late(today)) for l in self.active_loans(member_id)]
        return {"member": member, "active": active, "unpaid": self.unpaid_fines(member_id)}

    def borrow_history(self, member_id):
        """Linked list of the member's loans, newest first (ordered by issue date)."""
        self.get_member(member_id)
        history = BorrowHistory()
        for loan in self.loan_repo.history_for_member(member_id):   # oldest first,
            history.insert_head(loan)                               # so the newest ends up at the head
        return history

    def category_tree(self):
        return build_tree(self.item_repo.all())

    def iter_overdue(self, today):
        """Generator: yields one overdue loan at a time."""
        yield from self.loan_repo.overdue(today)

    def overdue_report(self, today):
        members, items = {}, {}
        rows = []
        for l in self.iter_overdue(today):
            m = members.setdefault(l.member_id, self.get_member(l.member_id))
            i = items.setdefault(l.isbn, self.get_item(l.isbn))
            rows.append(OverdueRow(l, m, i, l.days_late(today), l.fine(today, m.fine_per_day(), i.price)))
        return sorted(rows, key=lambda r: (-r.days, r.loan.loan_id))  # most days late first

    def items_by_category(self):
        pairs = sorted((i.category, i.title) for i in self.item_repo.all())
        grouped = defaultdict(list)
        for category, title in pairs:
            grouped[category].append(title)
        return dict(grouped)

    def members_with_unpaid_fines(self):
        owed = [(self.get_member(mid), amount) for mid, amount in self.loan_repo.members_with_unpaid()]
        return sorted(owed, key=lambda pair: -pair[1])
