"""Reproduces every Phase 2 sample.   TODAY=2026-10-12 python demo_phase2.py"""
import os
import sys
from datetime import date

from dsa.categories import count_items, path_to, print_tree
from dsa.hashing import (format_group_by_author, format_most_borrowed, format_reading_challenge,
                         import_books, most_borrowed)
from dsa.recursion import factorial, fibonacci, sum_of_digits
from dsa.search import binary_search_counted
from dsa.sorting import bubble_sort, format_catalogue_sort, insertion_sort, selection_sort
from library import Library

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
TODAY = date.fromisoformat(os.environ.get("TODAY", "2026-10-12"))
HERE = os.path.dirname(os.path.abspath(__file__))


def fresh():
    lib = Library()
    lib.load_data(os.path.join(HERE, "data"))
    return lib


lib = fresh()
print("--- 2.2 sorting by hand")
for sort in (bubble_sort, insertion_sort, selection_sort):
    sort([5, 2, 4, 1])
    print()
print("--- 2.2 binary search")
isbns = sorted(lib.items)
for target in ("9780000000066", "9780000000050"):
    idx, comps = binary_search_counted(isbns, target)
    print(f"binary_search(isbns, {target!r}) -> {idx}    ({comps} comparisons)")
print("binary_search([], '9780000000011') ->", binary_search_counted([], "9780000000011")[0],
      "   (%d comparisons)" % binary_search_counted([], "x")[1])
print("\n--- 2.2 catalogue sort")
print(format_catalogue_sort(lib.items.values()))

print("\n--- 2.3 hashing")
_, messages, summary = import_books(os.path.join(HERE, "books_with_duplicate.csv"))
print("\n".join(messages + [summary]))
print("\ngroup_by_author():")
print(format_group_by_author(lib.items.values()))
print("\nmost_borrowed(3):")
print(format_most_borrowed(most_borrowed(lib.loans, lib.items, 3)))
print()
for target in (724, 720, 1000):
    print(f"reading_challenge({target}) -> {format_reading_challenge(lib.items.values(), target)}")

print("\n--- 2.4 undo, waiting list, borrow history")
lib = fresh()
lib.borrow("M001", "9780000000011", TODAY)
print(lib.undo())
print(lib.undo() or "Nothing to undo.")
lib = fresh()
lib.reserve("M003", "9780000000028")
lib.reserve("M001", "9780000000028")
alch = "9780000000028"
print(f"\nWaiting list for 'The Alchemist': {', '.join(lib.waiting_names(alch))}")
res = lib.return_item("L001", TODAY)
print(f"Next on waiting list: {res.next_member.name}.")
print(f"Waiting list for 'The Alchemist': {', '.join(lib.waiting_names(alch))}")
for mid in ("M002", "M003"):
    print(f"\nBorrow history, {lib.members[mid].name} (newest first):")
    print(lib.borrow_history(mid))

print("\n--- 2.5 recursion")
print("factorial(5)        ->", factorial(5))
print("fibonacci(7)        ->", fibonacci(7))
print("sum_of_digits(4096) ->", sum_of_digits(4096))
tree = lib.category_tree()
print("\nprint_tree(root):")
print_tree(tree)
print(f"\ncount_items('Technology')            -> {count_items(tree, 'Technology')}")
print(f"path_to('Software Engineering')      -> {path_to(tree, 'Software Engineering')}")
print(f"path_to('Cooking')                   -> {path_to(tree, 'Cooking')}")
