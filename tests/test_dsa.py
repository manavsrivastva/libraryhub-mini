import os
import tempfile
from datetime import date

import pytest

from conftest import ALCHEMIST, DATA, PYTHON, WINGS
from dsa.categories import (build_tree, count_items, count_items_iter, path_to, print_tree,
                            tree_lines)
from dsa.hashing import (build_word_index, format_group_by_author, format_most_borrowed,
                         format_reading_challenge, import_books, most_borrowed, search_index)
from dsa.history import BorrowHistory
from dsa.recursion import factorial, factorial_iter, fibonacci, fibonacci_memo, sum_of_digits
from dsa.search import binary_search, binary_search_counted, linear_search, linear_search_title
from dsa.sorting import (bubble_sort, catalogue_sort, format_catalogue_sort, insertion_sort,
                         selection_sort)
from loans import Loan

TODAY = date(2026, 10, 12)
ISBNS = ["9780000000011", "9780000000028", "9780000000035", "9780000000042",
         "9780000000059", "9780000000066", "9780000000073"]


# ---------------------------------------------------------------- search
@pytest.mark.parametrize("seq, target, expected", [
    ([], 5, -1),            # empty list
    ([5], 5, 0),            # one element
    ([5, 6, 7], 5, 0),      # first
    ([5, 6, 7], 7, 2),      # last
    ([5, 6, 7], 9, -1),     # not found
])
def test_linear_and_binary_search_edge_cases(seq, target, expected):
    assert linear_search(seq, target) == expected
    assert binary_search(seq, target) == expected


def test_binary_search_sample_comparisons():
    assert binary_search_counted(ISBNS, "9780000000066") == (5, 2)
    assert binary_search_counted(ISBNS, "9780000000050") == (-1, 3)
    assert binary_search_counted([], "9780000000011") == (-1, 0)


def test_linear_search_title_is_case_insensitive(lib):
    items = list(lib.items.values())
    assert linear_search_title(items, "sapiens") == 4
    assert linear_search_title(items, "nothing") == -1


# ---------------------------------------------------------------- sorting
def test_bubble_sort_prints_every_pass(capsys):
    assert bubble_sort([5, 2, 4, 1]) == [1, 2, 4, 5]
    assert capsys.readouterr().out == (
        "bubble_sort([5, 2, 4, 1])\n  after pass 1: [2, 4, 1, 5]\n"
        "  after pass 2: [2, 1, 4, 5]\n  after pass 3: [1, 2, 4, 5]\n")


def test_insertion_sort_prints_every_pass(capsys):
    insertion_sort([5, 2, 4, 1])
    assert capsys.readouterr().out == (
        "insertion_sort([5, 2, 4, 1])\n  after inserting index 1: [2, 5, 4, 1]\n"
        "  after inserting index 2: [2, 4, 5, 1]\n  after inserting index 3: [1, 2, 4, 5]\n")


def test_selection_sort_prints_every_pass(capsys):
    selection_sort([5, 2, 4, 1])
    assert capsys.readouterr().out == (
        "selection_sort([5, 2, 4, 1])\n  after pass 1 (min=1): [1, 2, 4, 5]\n"
        "  after pass 2 (min=2): [1, 2, 4, 5]\n  after pass 3 (min=4): [1, 2, 4, 5]\n")


@pytest.mark.parametrize("sort", [bubble_sort, insertion_sort, selection_sort])
@pytest.mark.parametrize("data", [[], [1], [3, 1, 2], [2, 2, 1], list(range(10, 0, -1))])
def test_hand_sorts_match_sorted(sort, data):
    assert sort(data, show=False) == sorted(data)


def test_catalogue_sort_matches_sample(lib):
    assert format_catalogue_sort(lib.items.values()) == (
        "Biography   Wings of Fire              180\n"
        "Fiction     The Alchemist              208\n"
        "History     Sapiens                    512\n"
        "Magazines   India Today (Oct 2026)      90\n"
        "Reference   Encyclopaedia of Science  1200\n"
        "Technology  Python Crash Course        544\n"
        "Technology  Clean Code                 464")
    assert catalogue_sort(lib.items.values())[-2].title == "Python Crash Course"


# ---------------------------------------------------------------- hashing
def test_import_reports_duplicate_line_number():
    path = os.path.join(DATA, "..", "books_with_duplicate.csv")
    items, messages, summary = import_books(path)
    assert messages == ["Line 9: duplicate ISBN 9780000000042 (already used by 'Python Crash Course'), skipped."]
    assert summary == "Imported 8 rows: 7 added, 1 duplicate skipped."
    assert len(items) == 7


def test_import_skips_invalid_rows():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "b.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("isbn,title,authors,category,parent_category,item_type,pages,price,total_copies\n"
                    "123,Bad,A,C,,Book,10,10,1\n"
                    "9780000000011,Good,A,C,,Book,10,10,1\n")
        items, messages, summary = import_books(path)
    assert len(items) == 1 and "Line 2" in messages[0] and "1 invalid skipped" in summary


def test_group_by_author(lib):
    text = format_group_by_author(lib.items.values())
    assert text.splitlines()[0] == "A.P.J. Abdul Kalam: Wings of Fire"
    assert "Various: Encyclopaedia of Science, India Today (Oct 2026)" in text
    assert len(text.splitlines()) == 7


def test_most_borrowed_breaks_ties_alphabetically(lib):
    assert most_borrowed(lib.loans, lib.items, 3) == [
        ("Python Crash Course", 3), ("Wings of Fire", 3), ("Clean Code", 1)]
    assert format_most_borrowed(most_borrowed(lib.loans, lib.items, 3)).splitlines()[2] == \
        "3. Clean Code           1"


@pytest.mark.parametrize("target, expected", [
    (724, "Wings of Fire (180) + Python Crash Course (544) = 724"),
    (720, "The Alchemist (208) + Sapiens (512) = 720"),
    (1000, "No pair found."),
])
def test_reading_challenge(lib, target, expected):
    assert format_reading_challenge(lib.items.values(), target) == expected


def test_reading_challenge_excludes_reference(lib):
    # 1200 pages + 90 = 1290 would only work with the Encyclopaedia
    assert format_reading_challenge(lib.items.values(), 1290) == "No pair found."


def test_word_index_multi_word_search(lib):
    index = build_word_index(lib.items.values())
    assert search_index(index, "crash python") == [PYTHON]
    assert search_index(index, "paulo coelho") == [ALCHEMIST]
    assert search_index(index, "paulo martin") == []


# ---------------------------------------------------------------- undo (stack)
def test_undo_borrow_restores_everything(lib, today):
    loan = lib.borrow("M001", WINGS, today)
    assert lib.items[WINGS].available == 1
    msg = lib.undo()
    assert msg == "Undid borrow of 'Wings of Fire' by Asha Raman (loan L011 removed)."
    assert lib.items[WINGS].available == 2 and lib.active_loans("M001") == []
    assert lib.borrow("M001", WINGS, today).loan_id == loan.loan_id   # number reused


def test_undo_with_nothing_to_undo(lib):
    assert lib.undo() is None


def test_undo_return_restores_fine_loan_and_queue(lib, today):
    lib.reserve("M003", ALCHEMIST)
    lib.reserve("M001", ALCHEMIST)
    lib.return_item("L001", today)
    assert lib.waiting_names(ALCHEMIST) == ["Asha Raman"] and lib.unpaid_fines("M002") == 100
    msg = lib.undo()
    assert msg == "Undid return of 'The Alchemist' by Rahul Mehta (loan L001 is on loan again)."
    assert lib.unpaid_fines("M002") == 0 and lib.items[ALCHEMIST].available == 0
    assert lib.waiting_names(ALCHEMIST) == ["Sneha Iyer", "Asha Raman"]    # Sneha back at the FRONT
    assert lib.get_open_loan("L001").return_date is None


def test_undo_is_last_in_first_out(lib, today):
    lib.borrow("M001", WINGS, today)
    lib.return_item("L003", today)
    assert "Undid return" in lib.undo()
    assert "Undid borrow" in lib.undo()
    assert lib.undo() is None


# ---------------------------------------------------------------- queue (R7)
def test_waiting_list_serves_in_order(lib, today):
    lib.reserve("M003", ALCHEMIST)
    lib.reserve("M001", ALCHEMIST)
    assert lib.waiting_names(ALCHEMIST) == ["Sneha Iyer", "Asha Raman"]
    assert lib.return_item("L001", today).next_member.name == "Sneha Iyer"
    assert lib.waiting_names(ALCHEMIST) == ["Asha Raman"]


# ---------------------------------------------------------------- linked list
def test_borrow_history_newest_first(lib):
    assert str(lib.borrow_history("M002")) == "L001 -> L007 -> L008 -> None"
    assert str(lib.borrow_history("M003")) == "L003 -> L006 -> None"
    assert str(lib.borrow_history("M005")) == "None"


def make_history(ids):
    h = BorrowHistory()
    for i in ids:
        h.insert_head(Loan(i, "M", WINGS, date(2026, 1, 1), date(2026, 1, 2)))
    return h


def test_linked_list_delete_reverse_and_second_from_end():
    h = make_history(["L1", "L2", "L3", "L4"])        # head is L4
    assert str(h) == "L4 -> L3 -> L2 -> L1 -> None"
    assert h.second_from_end().loan_id == "L2"
    assert h.delete("L3") and not h.delete("L9") and len(h) == 3
    h.reverse()
    assert str(h) == "L1 -> L2 -> L4 -> None"
    assert h.delete("L1") and str(h) == "L2 -> L4 -> None"


# ---------------------------------------------------------------- recursion and tree
@pytest.mark.parametrize("n, expected", [(0, 1), (1, 1), (5, 120), (10, 3628800)])
def test_factorial(n, expected):
    assert factorial(n) == expected == factorial_iter(n)


@pytest.mark.parametrize("n, expected", [(0, 0), (1, 1), (7, 13), (20, 6765)])
def test_fibonacci(n, expected):
    assert fibonacci_memo(n) == expected
    if n <= 20:
        assert fibonacci(n) == expected


def test_sum_of_digits():
    assert sum_of_digits(4096) == 19 and sum_of_digits(7) == 7


def test_recursion_limit_vs_iteration():
    with pytest.raises(RecursionError):
        factorial(50_000)             # too deep for the call stack
    assert factorial_iter(5_000) > 0   # a loop has no such limit


def test_category_tree(lib, capsys):
    tree = lib.category_tree()
    print_tree(tree)
    assert capsys.readouterr().out == (
        "Library (7)\n  Biography (1)\n  Fiction (1)\n  History (1)\n  Magazines (1)\n"
        "  Reference (1)\n  Technology (2)\n    Programming (1)\n    Software Engineering (1)\n")
    assert count_items(tree, "Technology") == 2 == count_items_iter(tree, "Technology")
    assert count_items(tree, "Library") == 7
    assert count_items(tree, "Cooking") == 0
    assert path_to(tree, "Software Engineering") == ["Library", "Technology", "Software Engineering"]
    assert path_to(tree, "Cooking") is None
