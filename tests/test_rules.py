from datetime import date, timedelta

import pytest

from conftest import ALCHEMIST, CLEAN, ENCYC, MAGAZINE, PYTHON, SAPIENS, WINGS
from errors import (BorrowLimitExceededError, DuplicateISBNError, DuplicateLoanError,
                    InvalidISBNError, ItemNotAvailableError, ItemNotBorrowableError,
                    ItemNotFoundError, LibraryError, LoanNotFoundError, MemberNotFoundError,
                    RenewalNotAllowedError, UnpaidFinesError)
from items import Book, Magazine, ReferenceItem
from loans import Loan
from members import PremiumMember, RegularMember, StudentMember

D = date.fromisoformat


# ---------------------------------------------------------------- loading
def test_load_counts_and_availability(lib):
    assert (len(lib.items), len(lib.members), len(lib.loans), len(lib.fines)) == (7, 5, 10, 4)
    out = {i.isbn: i.available for i in lib.items.values()}
    assert out[ALCHEMIST] == 0 and out[PYTHON] == 1 and out[SAPIENS] == 0 and out[WINGS] == 2


# ---------------------------------------------------------------- worked examples
@pytest.mark.parametrize("member_cls, item_cls, expected", [
    (StudentMember, Book, "2026-10-26"),
    (RegularMember, Book, "2026-11-02"),
    (PremiumMember, Book, "2026-11-11"),
    (PremiumMember, Magazine, "2026-10-19"),   # R2
])
def test_due_date_table(member_cls, item_cls, expected):
    member = member_cls("MX", "Test", "t@example.com")
    item = item_cls(WINGS, "T", ["A"], "C", "", 10, 100, 1)
    assert D("2026-10-12") + timedelta(days=item.loan_days(member)) == D(expected)


@pytest.mark.parametrize("member_cls, price, due, returned, days, fine", [
    (StudentMember, 250, "2026-10-05", "2026-10-05", 0, 0),     # R10
    (StudentMember, 250, "2026-10-05", "2026-10-06", 1, 2),
    (RegularMember, 300, "2026-09-22", "2026-10-12", 20, 100),
    (PremiumMember, 600, "2026-09-01", "2026-10-01", 30, 90),
    (StudentMember, 80, "2026-07-08", "2026-09-06", 60, 80),    # R5 cap at price
])
def test_fine_table(member_cls, price, due, returned, days, fine):
    member = member_cls("MX", "Test", "t@example.com")
    loan = Loan("L999", "MX", WINGS, D(due) - timedelta(days=7), D(due))
    assert loan.days_late(D(returned)) == days
    assert loan.fine(D(returned), member.fine_per_day(), price) == fine


# ---------------------------------------------------------------- R1 .. R10
def test_r1_reference_item_cannot_be_borrowed(lib, today):
    with pytest.raises(ItemNotBorrowableError, match="reference item") as e:
        lib.borrow("M003", ENCYC, today)
    assert e.value.label == "R1"


def test_r2_magazine_cannot_be_renewed(lib, today):
    loan = lib.borrow("M003", MAGAZINE, today)
    assert loan.due_date == D("2026-10-19")
    with pytest.raises(RenewalNotAllowedError, match="Magazines cannot be renewed.") as e:
        lib.renew(loan.loan_id)
    assert e.value.label == "R2"


def test_r3_borrow_limit(lib, today):
    for isbn in (WINGS, CLEAN, MAGAZINE):
        lib.borrow("M001", isbn, today)
    with pytest.raises(BorrowLimitExceededError, match="already has 3 of 3 items on loan.") as e:
        lib.borrow("M001", PYTHON, today)
    assert e.value.label == "R3"


def test_r4_unpaid_fines_block(lib, today):
    with pytest.raises(UnpaidFinesError, match=r"unpaid fines of ₹120 \(limit ₹100\)") as e:
        lib.borrow("M004", CLEAN, today)
    assert e.value.label == "R4"


def test_r4_boundary_exactly_100_is_allowed(lib, today):
    lib.return_item("L001", today)             # Rahul's fine is exactly ₹100
    assert lib.unpaid_fines("M002") == 100
    assert lib.borrow("M002", WINGS, today).loan_id == "L011"


def test_r5_fine_saved_on_return_and_capped(lib, today):
    res = lib.return_item("L001", today)
    assert (res.days_late, res.fine) == (20, 100)
    assert {"loan_id": "L001", "amount": 100, "paid": False} in lib.fines


def test_r6_renewal_adds_loan_period_and_stops_at_two(lib, today):
    due = lib.renew("L003").due_date
    assert due == D("2026-11-19")                          # Premium: +30 days
    assert lib.renew("L003").due_date == D("2026-12-19")
    with pytest.raises(RenewalNotAllowedError, match="already been renewed 2 times") as e:
        lib.renew("L003")
    assert e.value.label == "R6"


def test_r6_waiting_list_blocks_renewal(lib):
    lib.reserve("M001", SAPIENS)
    with pytest.raises(RenewalNotAllowedError, match="another member is waiting"):
        lib.renew("L003")


def test_r7_waiting_list_is_first_come_first_served(lib, today):
    assert lib.reserve("M003", ALCHEMIST) == 1
    assert lib.reserve("M001", ALCHEMIST) == 2
    res = lib.return_item("L001", today)
    assert res.next_member.name == "Sneha Iyer"
    with pytest.raises(ItemNotAvailableError):             # copy is held for Sneha, not Asha
        lib.borrow("M001", ALCHEMIST, today)
    assert lib.borrow("M003", ALCHEMIST, today).isbn == ALCHEMIST


def test_r8_duplicate_title(lib, today):
    lib.borrow("M001", WINGS, today)
    with pytest.raises(DuplicateLoanError, match="already has a copy of 'Wings of Fire'") as e:
        lib.borrow("M001", WINGS, today)
    assert e.value.label == "R8"


@pytest.mark.parametrize("bad", ["123", "97800000000112", "97800000000AB", ""])
def test_r9_isbn_must_be_13_digits(lib, today, bad):
    with pytest.raises(InvalidISBNError, match="exactly 13 digits"):
        lib.borrow("M001", bad, today)


def test_r9_isbn_is_unique(lib):
    with pytest.raises(DuplicateISBNError):
        lib.add_item(Book(WINGS, "Copy", ["X"], "Biography", "", 10, 10, 1))


def test_r10_returning_on_due_date_is_not_late(lib):
    res = lib.return_item("L003", D("2026-10-20"))
    assert (res.days_late, res.fine) == (0, 0)


# ---------------------------------------------------------------- the other exceptions
def test_member_not_found(lib, today):
    with pytest.raises(MemberNotFoundError, match="No member with ID M009."):
        lib.borrow("M009", WINGS, today)


def test_item_not_found(lib, today):
    with pytest.raises(ItemNotFoundError, match="No item with ISBN 9780000000999."):
        lib.borrow("M001", "9780000000999", today)


def test_item_not_available(lib, today):
    with pytest.raises(ItemNotAvailableError, match="No copies of 'The Alchemist' are available."):
        lib.borrow("M003", ALCHEMIST, today)


def test_loan_not_found_and_already_returned(lib, today):
    with pytest.raises(LoanNotFoundError):
        lib.return_item("L999", today)
    with pytest.raises(LoanNotFoundError):
        lib.return_item("L004", today)            # already returned


def test_all_errors_share_one_parent():
    for cls in (InvalidISBNError, ItemNotFoundError, MemberNotFoundError, ItemNotBorrowableError,
                UnpaidFinesError, BorrowLimitExceededError, DuplicateLoanError,
                ItemNotAvailableError, RenewalNotAllowedError):
        assert issubclass(cls, LibraryError)


# ---------------------------------------------------------------- check order
def test_check_order_r4_reported_before_r3(lib, today):
    # Karthik owes > 100 AND the reference check passes; R4 must win over availability etc.
    with pytest.raises(UnpaidFinesError):
        lib.borrow("M004", ALCHEMIST, today)


# ---------------------------------------------------------------- validation
def test_property_validation():
    with pytest.raises(ValueError):
        Book(WINGS, "  ", ["A"], "C", "", 10, 10, 1)       # blank title
    with pytest.raises(ValueError):
        Book(WINGS, "T", ["A"], "C", "", 10, 10, -1)       # negative copies
    with pytest.raises(InvalidISBNError):
        Book("123", "T", ["A"], "C", "", 10, 10, 1)
    with pytest.raises(ValueError):
        StudentMember("M1", "Name", "no-at-sign")
    assert "Wings" in str(Book(WINGS, "Wings", ["A"], "C", "", 10, 10, 1))
    assert "Book(" in repr(Book(WINGS, "Wings", ["A"], "C", "", 10, 10, 1))
    assert isinstance(ReferenceItem(WINGS, "R", ["A"], "C", "", 10, 10, 1).is_borrowable(), bool)


def test_no_type_checks_in_source():
    import pathlib
    for name in ("library.py", "main.py", "loans.py", "items.py"):
        assert "member_type ==" not in pathlib.Path(name).read_text(encoding="utf-8")


# ---------------------------------------------------------------- Pythonic layer
def test_audit_logs_success_only(lib, today):
    with pytest.raises(ItemNotBorrowableError):
        lib.borrow("M003", ENCYC, today)
    assert lib.audit_log == []
    loan = lib.borrow("M001", WINGS, today)
    lib.renew(loan.loan_id)
    lib.return_item(loan.loan_id, today)
    assert [e["action"] for e in lib.audit_log] == ["borrow", "renew", "return"]
    assert lib.audit_log[0]["member"] == "M001" and lib.audit_log[0]["item"] == WINGS


def test_iter_overdue_is_a_generator(lib, today):
    gen = lib.iter_overdue(today)
    assert iter(gen) is gen
    assert [l.loan_id for l in gen] == ["L001", "L002"]


def test_overdue_report_sorted_and_fines(lib, today):
    rows = lib.overdue_report(today)
    assert [(r.loan.loan_id, r.days, r.fine) for r in rows] == [("L001", 20, 100), ("L002", 7, 14)]


def test_search_is_case_insensitive_on_title_and_author(lib):
    assert [i.title for i in lib.search("PAULO")] == ["The Alchemist"]
    assert [i.title for i in lib.search("crash")] == ["Python Crash Course"]
    assert lib.search("zzz") == []


def test_reports_by_category_and_unpaid(lib):
    cats = lib.items_by_category()
    assert cats["Programming"] == ["Python Crash Course"]
    assert [(m.name, amt) for m, amt in lib.members_with_unpaid_fines()] == [("Karthik N", 120)]


def test_new_loan_ids_continue_the_sequence(lib, today):
    assert lib.borrow("M001", WINGS, today).loan_id == "L011"
    assert lib.borrow("M001", MAGAZINE, today).loan_id == "L012"
