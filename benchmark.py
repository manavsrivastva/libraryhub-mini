"""Complexity audit.   python benchmark.py          (full: a few minutes)
                       python benchmark.py --quick  (small sizes, seconds)

Writes benchmark_results.md. Write your PREDICTIONS in BENCHMARK.md BEFORE you run this.
"""
import sys
import time
from collections import deque
from datetime import date

from dsa.search import binary_search, linear_search_title
from dsa.sorting import bubble_sort, insertion_sort, selection_sort
from generate_books import generate_books
from phase2_library import Library
from loans import Loan
from members import PremiumMember

TODAY = date(2026, 10, 12)
OUT = []


def say(line=""):
    print(line)
    OUT.append(line)


def ms(fn, repeat=1):
    start = time.perf_counter()
    for _ in range(repeat):
        fn()
    return (time.perf_counter() - start) * 1000 / repeat


def build_library(n):
    """n items, n/10 members holding n/2 overdue loans, plus 30 members with no loans."""
    lib = Library()
    books = generate_books(n)
    for b in books:
        lib.add_item(b)
    holders = max(10, n // 10)
    for i in range(holders):
        lib.add_member(PremiumMember(f"B{i:06d}", f"Member {i}", f"m{i}@example.com"))
    for i in range(30):
        lib.add_member(PremiumMember(f"F{i:03d}", f"Free {i}", f"f{i}@example.com"))
    open_loans = n // 2
    for i in range(open_loans):
        loan = Loan(f"L{i + 1:06d}", f"B{i % holders:06d}", books[i].isbn, date(2026, 8, 1), date(2026, 8, 31))
        lib.items[books[i].isbn].available -= 1
        lib._register_loan(loan)
    Loan.reset_counter(open_loans + 1)
    return lib, books


def audit(sizes):
    say("## 2.1 Complexity audit (milliseconds per call)")
    say("")
    say("| Method | Predicted time | Predicted space | " + " | ".join(f"n={n:,}" for n in sizes) + " | last/first |")
    say("|---|---|---|" + "---|" * (len(sizes) + 1))
    methods = [("list_items", "O(n)", "O(n)"), ("search (miss)", "O(n)", "O(1)"),
               ("borrow", "O(1)", "O(1)"), ("return_item", "O(1)", "O(1)"),
               ("overdue_report", "O(L + k log k)", "O(k)")]
    results = {name: [] for name, _, _ in methods}
    for n in sizes:
        lib, books = build_library(n)
        results["list_items"].append(ms(lib.list_items, 3))
        results["search (miss)"].append(ms(lambda: lib.search("zzzz"), 3))
        start = time.perf_counter()
        for k in range(20):
            lib.borrow(f"F{k:03d}", books[n // 2 + k].isbn, TODAY)
        results["borrow"].append((time.perf_counter() - start) * 1000 / 20)
        start = time.perf_counter()
        for k in range(20):
            lib.return_item(f"L{k + 1:06d}", TODAY)
        results["return_item"].append((time.perf_counter() - start) * 1000 / 20)
        results["overdue_report"].append(ms(lambda: lib.overdue_report(TODAY), 1))
    for name, big_o, space in methods:
        t = results[name]
        ratio = t[-1] / t[0] if t[0] else float("nan")
        say(f"| {name} | {big_o} | {space} | " + " | ".join(f"{x:.4f}" for x in t) + f" | x{ratio:.1f} |")
    say("")
    say(f"`last/first` compares n={sizes[-1]:,} with n={sizes[0]:,} (a {sizes[-1] // sizes[0]}x bigger library).")


def search_and_sort(sizes, slow_limit):
    say("")
    say("## 2.2 Searching and sorting (milliseconds)")
    say("")
    say("| n | linear_search | binary_search | sorted(key) | insertion | bubble | selection |")
    say("|---|---|---|---|---|---|---|")
    for n in sizes:
        books = generate_books(n)
        titles = [b.title for b in books][::-1]            # reversed: a hard case for the hand sorts
        last_title = books[-1].title
        isbns = sorted(b.isbn for b in books)
        linear = ms(lambda: linear_search_title(books, last_title), 20)
        binary = ms(lambda: binary_search(isbns, "9780000000050"), 2000)
        builtin = ms(lambda: sorted(titles), 5)
        cells = []
        for fn in (insertion_sort, bubble_sort, selection_sort):
            cells.append(f"{ms(lambda: fn(titles, show=False)):.1f}" if n <= slow_limit else "skipped")
        say(f"| {n:,} | {linear:.4f} | {binary:.4f} | {builtin:.3f} | " + " | ".join(cells) + " |")


def pop_benchmark(n=100_000):
    say("")
    say(f"## 2.4 list.pop(0) vs deque.popleft() on {n:,} entries")
    items = list(range(n))
    t_list = ms(lambda: [items.pop(0) for _ in range(n)])
    queue = deque(range(n))
    t_deque = ms(lambda: [queue.popleft() for _ in range(n)])
    say("")
    say(f"list.pop(0): {t_list:.1f} ms   deque.popleft(): {t_deque:.1f} ms   ratio: x{t_list / max(t_deque, 0.001):.0f}")


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    sizes = [1000, 2000] if quick else [1000, 5000, 10000, 50000]
    sort_sizes = [500, 1000] if quick else [1000, 5000, 10000]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    audit(sizes)
    search_and_sort(sort_sizes, slow_limit=10000)
    pop_benchmark(20_000 if quick else 100_000)
    with open("benchmark_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(OUT) + "\n")
    print("\nSaved benchmark_results.md")
