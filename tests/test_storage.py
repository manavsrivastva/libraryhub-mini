"""Phase 3 Part B: the storage package under the Library."""
import os
import re
import tempfile
from datetime import date

import pytest

import main
from conftest import ALCHEMIST, DATA, SAPIENS, WINGS
from errors import ItemNotAvailableError
from library import Library
from members import MEMBER_TYPES
from storage import Database

TODAY = date(2026, 10, 12)
HERE = os.path.join(os.path.dirname(__file__), "..")


def open_library(path):
    lib = Library(Database(path))
    if lib.item_repo.count() == 0:
        lib.load_data(DATA)
    return lib


# ---------------------------------------------------------------- persistence (the sheet's sample)
def test_data_survives_closing_and_reopening_the_program():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "library.db")
        first = open_library(path)
        first.borrow("M001", WINGS, TODAY)
        first.db.close()                                   # "close the program"

        second = open_library(path)                        # "reopen it"
        assert second.counts() == {"items": 7, "members": 5, "loans": 11, "fines": 4}
        assert main.format_member_loans(second.member_loans("M001", TODAY)) == (
            "Loans for Asha Raman (Student: 3 items, 14 days, ₹2/day)\n"
            "LOAN  TITLE          ISSUED      DUE         STATUS\n"
            "L011  Wings of Fire  2026-10-12  2026-10-26  On loan\n"
            "Active loans: 1 of 3\n"
            "Unpaid fines: ₹0")
        second.db.close()


def test_waiting_list_and_held_copy_survive_a_restart():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "library.db")
        first = open_library(path)
        first.reserve("M003", ALCHEMIST)
        first.reserve("M001", ALCHEMIST)
        first.return_item("L001", TODAY)                   # Sneha is notified, the copy is held for her
        first.db.close()

        second = open_library(path)
        assert second.waiting_names(ALCHEMIST) == ["Asha Raman"]
        with pytest.raises(ItemNotAvailableError):         # still held for Sneha after the restart
            second.borrow("M001", ALCHEMIST, TODAY)
        assert second.borrow("M003", ALCHEMIST, TODAY).isbn == ALCHEMIST
        second.db.close()


def test_audit_log_is_stored_in_the_database():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "library.db")
        first = open_library(path)
        first.borrow("M001", WINGS, TODAY)
        first.db.close()
        second = open_library(path)
        assert [e["action"] for e in second.audit_log] == ["borrow"]
        second.db.close()


# ---------------------------------------------------------------- one unit: commit or roll back
def test_a_failure_halfway_rolls_the_whole_borrow_back(lib, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("audit insert failed")
    monkeypatch.setattr(lib.audit_repo, "add", boom)       # the LAST statement of the transaction fails
    with pytest.raises(RuntimeError):
        lib.borrow("M001", WINGS, TODAY)
    assert lib.loan_repo.count() == 10                     # the loan insert was undone too
    assert lib.items[WINGS].available == 2
    assert lib.undo_stack == []                            # a rolled-back operation is not undoable


def test_transaction_context_manager_commits_and_rolls_back():
    db = Database()
    with db.transaction():
        db.execute("INSERT INTO authors (name) VALUES ('A')")
    assert db.one("SELECT COUNT(*) FROM authors") == 1
    with pytest.raises(ValueError):
        with db.transaction():
            db.execute("INSERT INTO authors (name) VALUES ('B')")
            raise ValueError("stop")
    assert db.one("SELECT COUNT(*) FROM authors") == 1


def test_nested_transactions_join_the_outer_one():
    db = Database()
    with pytest.raises(ValueError):
        with db.transaction():
            with db.transaction():
                db.execute("INSERT INTO authors (name) VALUES ('inner')")
            raise ValueError("outer fails after the inner block finished")
    assert db.one("SELECT COUNT(*) FROM authors") == 0


# ---------------------------------------------------------------- the database is the single source of truth
def test_every_test_gets_its_own_database():
    a, b = Library(), Library()
    a.load_data(DATA)
    assert a.item_repo.count() == 7 and b.item_repo.count() == 0


def test_foreign_keys_are_switched_on():
    assert Database().one("PRAGMA foreign_keys") == 1


def test_membership_types_table_agrees_with_the_member_classes():
    db = Database()
    rows = {r[0]: r[1:] for r in db.execute("SELECT type_name, max_items, loan_days, fine_per_day FROM membership_types")}
    assert set(rows) == set(MEMBER_TYPES)
    for name, cls in MEMBER_TYPES.items():
        m = cls("X", "x", "x@x")
        assert rows[name] == (m.max_items(), m.loan_days(), m.fine_per_day())


def test_availability_is_calculated_from_loans_never_stored(lib):
    assert lib.items[ALCHEMIST].available == 0
    lib.return_item("L001", TODAY)
    assert lib.items[ALCHEMIST].available == 1
    lib.undo()
    assert lib.items[ALCHEMIST].available == 0


def test_reserved_copy_does_not_show_as_free(lib):
    lib.reserve("M003", ALCHEMIST)
    lib.return_item("L001", TODAY)
    assert dict((r[0], r[3]) for r in lib.list_items())[ALCHEMIST] == "0 of 1"


def test_undo_survives_the_database_round_trip_of_a_held_copy(lib):
    lib.reserve("M003", ALCHEMIST)
    lib.return_item("L001", TODAY)
    lib.borrow("M003", ALCHEMIST, TODAY)                   # Sneha takes her held copy
    lib.undo()                                             # undo her borrow: the copy is held for her again
    with pytest.raises(ItemNotAvailableError):
        lib.borrow("M001", ALCHEMIST, TODAY)
    assert lib.borrow("M003", ALCHEMIST, TODAY).isbn == ALCHEMIST


# ---------------------------------------------------------------- no SQL built from strings
def test_no_sql_is_built_with_string_formatting():
    pattern = re.compile(r"""execute(?:many|script)?\(\s*f["']|execute(?:many)?\([^)]*["']\s*%\s|\.format\(""")
    files = [os.path.join(HERE, "library.py")]
    storage_dir = os.path.join(HERE, "storage")
    files += [os.path.join(storage_dir, n) for n in os.listdir(storage_dir) if n.endswith(".py")]
    for path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        assert not pattern.search(text), f"string-built SQL in {path}"
