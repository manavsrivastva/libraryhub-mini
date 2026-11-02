"""The Library: owns the data and enforces the Rulebook. It never reads the clock;
every date-dependent method receives `today` from the caller."""
import csv
import functools
import os
from collections import defaultdict, deque, namedtuple
from datetime import date, datetime, timedelta

from errors import (BorrowLimitExceededError, DuplicateISBNError, DuplicateLoanError,
                    InvalidISBNError, ItemNotAvailableError, ItemNotBorrowableError,
                    ItemNotFoundError, LoanNotFoundError, MemberNotFoundError,
                    RenewalNotAllowedError, UnpaidFinesError)
from dsa.categories import build_tree
from dsa.history import BorrowHistory
from items import ITEM_TYPES
from loans import Loan
from members import MEMBER_TYPES

FINE_LIMIT = 100  # R4: unpaid fines ABOVE this block borrowing

ReturnResult = namedtuple("ReturnResult", "loan days_late fine next_member")
OverdueRow = namedtuple("OverdueRow", "loan member item days fine")


def audit(action):
    """Decorator: record (time, action, member, item) after a method SUCCEEDS.
    If the method raises, the exception passes through and nothing is logged."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            loan = getattr(result, "loan", result)  # ReturnResult has .loan, Loan is the loan
            self.audit_log.append({
                "time": datetime.now().isoformat(timespec="seconds"),
                "action": action,
                "member": loan.member_id,
                "item": loan.isbn,
            })
            return result
        return wrapper
    return decorator


class Library:
    def __init__(self):
        self.items = {}                      # dict by ISBN: O(1) lookup by key
        self.members = {}                    # dict by member ID
        self.loans = []                      # list: ordered history, appended in time order
        self.loan_index = {}                 # dict loan_id -> Loan: O(1) instead of scanning the list
        self.active = defaultdict(dict)      # member_id -> {isbn: open Loan}: O(1) for R3 and R8
        self._unpaid = defaultdict(int)      # member_id -> unpaid fines, kept up to date (R4)
        self.undo_stack = []                 # stack: last borrow/return operations (LIFO)
        self.isbns = set()                   # set: fast "is this ISBN taken?" (R9)
        self.fines = []                      # [{"loan_id", "amount", "paid"}]
        self.waiting = defaultdict(deque)    # isbn -> queue of member IDs (R7, first in first out)
        self.held = defaultdict(list)        # isbn -> member IDs a returned copy is held for
        self.audit_log = []
        Loan.reset_counter(1)

    # ---------------------------------------------------------------- loading
    def add_item(self, item):
        if item.isbn in self.isbns:
            raise DuplicateISBNError(f"ISBN {item.isbn} already exists.")  # R9
        self.items[item.isbn] = item
        self.isbns.add(item.isbn)

    def add_member(self, member):
        self.members[member.member_id] = member

    def load_data(self, data_dir):
        def rows(name):
            with open(os.path.join(data_dir, name), newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))

        for r in rows("books.csv"):
            item_cls = ITEM_TYPES[r["item_type"]]
            self.add_item(item_cls(r["isbn"], r["title"], r["authors"].split(";"), r["category"],
                                   r["parent_category"], r["pages"], r["price"], r["total_copies"]))
        for r in rows("members.csv"):
            self.add_member(MEMBER_TYPES[r["membership_type"]](r["member_id"], r["name"], r["email"]))
        for r in rows("loans.csv"):
            ret = date.fromisoformat(r["return_date"]) if r["return_date"] else None
            self._register_loan(Loan(r["loan_id"], r["member_id"], r["isbn"],
                                     date.fromisoformat(r["issue_date"]),
                                     date.fromisoformat(r["due_date"]), ret))
        for r in rows("fines.csv"):
            fine = {"loan_id": r["loan_id"], "amount": int(r["amount"]),
                    "paid": r["paid"].strip().lower() == "yes"}
            self.fines.append(fine)
            if not fine["paid"]:
                self._unpaid[self.loan_index[fine["loan_id"]].member_id] += fine["amount"]

        # Rebuild availability: every loan without a return date has one copy out.
        for loan in self.loans:
            if loan.is_open:
                self.items[loan.isbn].available -= 1
        Loan.reset_counter(max(int(l.loan_id[1:]) for l in self.loans) + 1)
        return {"items": len(self.items), "members": len(self.members),
                "loans": len(self.loans), "fines": len(self.fines)}

    def _register_loan(self, loan):
        """Every place that adds a loan goes through here, so the indexes never drift apart."""
        self.loans.append(loan)
        self.loan_index[loan.loan_id] = loan
        if loan.is_open:
            self.active[loan.member_id][loan.isbn] = loan

    # ---------------------------------------------------------------- lookups
    def get_member(self, member_id):
        try:
            return self.members[member_id]
        except KeyError:
            raise MemberNotFoundError(f"No member with ID {member_id}.") from None

    def get_item(self, isbn):
        if len(isbn) != 13 or not isbn.isdigit():
            raise InvalidISBNError("ISBN must be exactly 13 digits.")
        try:
            return self.items[isbn]
        except KeyError:
            raise ItemNotFoundError(f"No item with ISBN {isbn}.") from None

    def get_open_loan(self, loan_id):
        loan = self.loan_index.get(loan_id)
        if loan is None or not loan.is_open:
            raise LoanNotFoundError(f"No open loan with ID {loan_id}.")
        return loan

    def active_loans(self, member_id):
        return list(self.active.get(member_id, {}).values())

    def unpaid_fines(self, member_id):
        return self._unpaid.get(member_id, 0)

    def waiting_names(self, isbn):
        return [self.members[mid].name for mid in self.waiting.get(isbn, ())]

    def free_copies(self, isbn):
        """Copies a walk-in member could take: not out on loan and not held for the queue."""
        return max(0, self.items[isbn].available - len(self.held[isbn]))

    # ---------------------------------------------------------------- catalogue
    def list_items(self):
        return [(i.isbn, i.title, i.type_name, i.availability_label(self.free_copies(i.isbn)))
                for i in self.items.values()]

    def search(self, text):
        q = text.strip().lower()
        hits = filter(lambda i: q in i.title.lower() or any(q in a.lower() for a in i.authors),
                      self.items.values())
        return list(hits) if q else []

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
        mine = self.active.get(member_id, {})
        if len(mine) >= member.max_items():                                   # R3
            raise BorrowLimitExceededError(
                f"{member.name} already has {len(mine)} of {member.max_items()} items on loan.")
        if isbn in mine:                                                      # R8
            raise DuplicateLoanError(f"{member.name} already has a copy of '{item.title}'.")
        held_for_me = member_id in self.held[isbn]                            # availability (R7)
        if not held_for_me and self.free_copies(isbn) == 0:
            raise ItemNotAvailableError(f"No copies of '{item.title}' are available.")
        held_index = None
        if held_for_me:
            held_index = self.held[isbn].index(member_id)
            self.held[isbn].remove(member_id)
        due = today + timedelta(days=item.loan_days(member))
        loan = Loan(Loan.new_id(), member_id, isbn, today, due)
        item.available -= 1
        self._register_loan(loan)
        # Undo needs a SNAPSHOT of what changed, not just the loan object.
        self.undo_stack.append({"op": "borrow", "loan": loan, "held_index": held_index})
        return loan

    @audit("return")
    def return_item(self, loan_id, today):
        loan = self.get_open_loan(loan_id)
        member, item = self.members[loan.member_id], self.items[loan.isbn]
        late = loan.days_late(today)
        fine = loan.fine(today, member.fine_per_day(), item.price)
        loan.return_date = today
        item.available += 1
        del self.active[loan.member_id][loan.isbn]
        fine_record = None
        if fine > 0:
            fine_record = {"loan_id": loan.loan_id, "amount": fine, "paid": False}
            self.fines.append(fine_record)
            self._unpaid[loan.member_id] += fine
        next_member = None
        if self.waiting[loan.isbn]:                      # R7: first in the queue is served first
            next_id = self.waiting[loan.isbn].popleft()  # deque.popleft(): O(1)
            self.held[loan.isbn].append(next_id)         # the copy is held for them
            next_member = self.members[next_id]
        self.undo_stack.append({"op": "return", "loan": loan, "fine": fine_record,
                                "next_id": next_member.member_id if next_member else None})
        return ReturnResult(loan, late, fine, next_member)

    def undo(self):
        """Reverse the latest borrow or return. Returns a message, or None if nothing to undo."""
        if not self.undo_stack:
            return None
        entry = self.undo_stack.pop()
        loan = entry["loan"]
        member, item = self.members[loan.member_id], self.items[loan.isbn]
        if entry["op"] == "borrow":
            if self.loans and self.loans[-1] is loan:
                self.loans.pop()
            else:
                self.loans.remove(loan)
            del self.loan_index[loan.loan_id]
            del self.active[loan.member_id][loan.isbn]
            item.available += 1
            if entry["held_index"] is not None:                  # give the held copy back
                self.held[loan.isbn].insert(entry["held_index"], loan.member_id)
            Loan.reset_counter(int(loan.loan_id[1:]))            # the number can be used again
            message = f"Undid borrow of '{item.title}' by {member.name} (loan {loan.loan_id} removed)."
        else:
            loan.return_date = None
            item.available -= 1
            self.active[loan.member_id][loan.isbn] = loan
            if entry["fine"] is not None:
                self.fines.remove(entry["fine"])
                self._unpaid[loan.member_id] -= entry["fine"]["amount"]
            if entry["next_id"] is not None:                     # first in the queue goes back to the FRONT
                self.held[loan.isbn].remove(entry["next_id"])
                self.waiting[loan.isbn].appendleft(entry["next_id"])
            message = f"Undid return of '{item.title}' by {member.name} (loan {loan.loan_id} is on loan again)."
        self.audit_log.append({"time": datetime.now().isoformat(timespec="seconds"),
                               "action": f"undo-{entry['op']}", "member": loan.member_id, "item": loan.isbn})
        return message

    @audit("renew")
    def renew(self, loan_id):
        loan = self.get_open_loan(loan_id)
        member, item = self.members[loan.member_id], self.items[loan.isbn]
        if not item.can_renew():                                              # R2 first
            raise RenewalNotAllowedError(f"{item.type_name}s cannot be renewed.", code="R2")
        if loan.renewals >= Loan.MAX_RENEWALS:                                # R6: limit
            raise RenewalNotAllowedError(
                f"'{item.title}' has already been renewed {Loan.MAX_RENEWALS} times.")
        if self.waiting[loan.isbn]:                                           # R6: someone waits
            raise RenewalNotAllowedError(
                f"'{item.title}' cannot be renewed because another member is waiting.")
        loan.due_date += timedelta(days=member.loan_days())
        loan.renewals += 1
        return loan

    def reserve(self, member_id, isbn):
        member = self.get_member(member_id)
        item = self.get_item(isbn)
        if not item.is_borrowable():
            raise ItemNotBorrowableError(f"'{item.title}' is a reference item and cannot be borrowed.")
        if isbn in self.active.get(member_id, {}):
            raise DuplicateLoanError(f"{member.name} already has a copy of '{item.title}'.")
        if member_id in self.waiting[isbn]:
            raise DuplicateLoanError(f"{member.name} is already on the waiting list for '{item.title}'.")
        self.waiting[isbn].append(member_id)
        return len(self.waiting[isbn])

    # ---------------------------------------------------------------- reports
    def member_loans(self, member_id, today):
        member = self.get_member(member_id)
        active = [(l, self.items[l.isbn], l.days_late(today)) for l in self.active_loans(member_id)]
        return {"member": member, "active": active, "unpaid": self.unpaid_fines(member_id)}

    def borrow_history(self, member_id):
        """Linked list of the member's loans, newest first (ordered by issue date)."""
        self.get_member(member_id)
        history = BorrowHistory()
        mine = sorted((l for l in self.loans if l.member_id == member_id),
                      key=lambda l: (l.issue_date, l.loan_id))
        for loan in mine:               # oldest first, so the newest ends up at the head
            history.insert_head(loan)
        return history

    def category_tree(self):
        return build_tree(self.items.values())

    def iter_overdue(self, today):
        """Generator: yields one overdue loan at a time."""
        for loan in self.loans:
            if loan.is_overdue(today):
                yield loan

    def overdue_report(self, today):
        rows = [OverdueRow(l, self.members[l.member_id], self.items[l.isbn], l.days_late(today),
                           l.fine(today, self.members[l.member_id].fine_per_day(), self.items[l.isbn].price))
                for l in self.iter_overdue(today)]
        return sorted(rows, key=lambda r: (-r.days, r.loan.loan_id))  # most days late first

    def items_by_category(self):
        pairs = sorted((i.category, i.title) for i in self.items.values())
        grouped = defaultdict(list)
        for category, title in pairs:
            grouped[category].append(title)
        return dict(grouped)

    def members_with_unpaid_fines(self):
        owed = {m.member_id: self.unpaid_fines(m.member_id) for m in self.members.values()}
        return sorted(((self.members[mid], amt) for mid, amt in owed.items() if amt > 0),
                      key=lambda pair: -pair[1])
