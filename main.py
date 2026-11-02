"""Console menu. Run with:  TODAY=2026-10-12 python main.py"""
import os
import sys
from datetime import date

from errors import ItemNotAvailableError, LibraryError
from library import Library
from storage import Database

MAX_OPTION = 9  # Phase 2 added option 9 (undo)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MENU = """=== LibraryHub Mini ===
1. List catalogue
2. Search by title or author
3. Borrow
4. Return
5. Renew
6. Join waiting list
7. Member loans
8. Overdue report
9. Undo last borrow/return
0. Exit"""


def get_today():
    raw = os.environ.get("TODAY")
    if not raw:
        return date.today()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        sys.exit(f"TODAY must look like 2026-10-12, not {raw!r}.")


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def format_table(headers, rows, right=()):
    widths = [max(len(str(c)) for c in col) for col in zip(headers, *rows)]

    def line(cells):
        parts = [str(c).rjust(w) if i in right else str(c).ljust(w)
                 for i, (c, w) in enumerate(zip(cells, widths))]
        return "  ".join(parts).rstrip()

    return "\n".join([line(headers)] + [line(r) for r in rows])


def ask(prompt):
    return input(prompt).strip()


# ------------------------------------------------------------------ handlers
def do_list(lib, today):
    print(format_table(["ISBN", "TITLE", "TYPE", "AVAILABLE"], lib.list_items()))


def do_search(lib, today):
    text = ask("Search: ")
    hits = lib.search(text)
    if not hits:
        print(f"No items match '{text}'.")
        return
    print(f"{plural(len(hits), 'result')}:")
    for i in hits:
        print(f"{i.isbn}  {i.title}  ({', '.join(i.authors)})  {i.availability_label(lib.free_copies(i.isbn))}")


def join_waiting_list(lib, member_id, isbn):
    position = lib.reserve(member_id, isbn)
    print(f"OK: {lib.get_member(member_id).name} is #{position} on the waiting list "
          f"for '{lib.get_item(isbn).title}'.")


def do_borrow(lib, today):
    member_id = ask("Member ID: ").upper()
    member = lib.get_member(member_id)          # fail early, before asking for the ISBN
    isbn = ask("ISBN: ")
    try:
        loan = lib.borrow(member_id, isbn, today)
    except ItemNotAvailableError as err:
        if ask(f"{err} Join waiting list? (y/n): ").lower() == "y":
            join_waiting_list(lib, member_id, isbn)
        else:
            print("Not added to the waiting list.")
        return
    print(f"OK: {member.name} borrowed '{lib.get_item(isbn).title}'. Due {loan.due_date}.")


def do_return(lib, today):
    res = lib.return_item(ask("Loan ID: ").upper(), today)
    name, title = lib.get_member(res.loan.member_id).name, lib.get_item(res.loan.isbn).title
    late = f"Late by {plural(res.days_late, 'day')}." if res.days_late else "Returned on time."
    print(f"OK: {name} returned '{title}'. {late} Fine: ₹{res.fine}.")
    if res.next_member:
        print(f"Next on waiting list: {res.next_member.name}.")
        remaining = lib.waiting_names(res.loan.isbn)
        if remaining:
            print(f"Waiting list for '{title}': {', '.join(remaining)}")


def do_renew(lib, today):
    loan = lib.renew(ask("Loan ID: ").upper())
    print(f"OK: Renewed '{lib.get_item(loan.isbn).title}' (renewal {loan.renewals} of 2). "
          f"New due date {loan.due_date}.")


def do_reserve(lib, today):
    member_id = ask("Member ID: ").upper()
    lib.get_member(member_id)
    join_waiting_list(lib, member_id, ask("ISBN: "))


def format_member_loans(view):
    m = view["member"]
    out = [f"Loans for {m.name} ({m.describe()})"]
    if view["active"]:
        rows = [(l.loan_id, item.title, l.issue_date, l.due_date,
                 f"OVERDUE ({plural(late, 'day')})" if late else "On loan")
                for l, item, late in view["active"]]
        out.append(format_table(["LOAN", "TITLE", "ISSUED", "DUE", "STATUS"], rows))
    out.append(f"Active loans: {len(view['active'])} of {m.max_items()}")
    out.append(f"Unpaid fines: ₹{view['unpaid']}")
    return "\n".join(out)


def do_member_loans(lib, today):
    print(format_member_loans(lib.member_loans(ask("Member ID: ").upper(), today)))


def format_overdue(rows, today):
    if not rows:
        return f"No overdue loans as of {today}."
    table = [(r.loan.loan_id, r.member.name, r.item.title, r.loan.due_date, r.days, f"₹{r.fine}")
             for r in rows]
    total = sum(map(lambda r: r.fine, rows))
    return (f"Overdue loans as of {today}\n"
            + format_table(["LOAN", "MEMBER", "TITLE", "DUE", "DAYS", "FINE SO FAR"], table, right={4})
            + f"\nTotal overdue: {len(rows)}   Fines so far: ₹{total}")


def do_overdue(lib, today):
    print(format_overdue(lib.overdue_report(today), today))


def do_undo(lib, today):
    message = lib.undo()
    print(f"OK: {message}" if message else "Nothing to undo.")


HANDLERS = {1: do_list, 2: do_search, 3: do_borrow, 4: do_return,
            5: do_renew, 6: do_reserve, 7: do_member_loans, 8: do_overdue, 9: do_undo}


def run_menu(lib, today):
    try:
        while True:
            choice = input("> ").strip()
            if not choice.isdigit() or int(choice) > MAX_OPTION:
                print(f"Please enter a number from 0 to {MAX_OPTION}.")
                continue
            if int(choice) == 0:
                return
            try:
                HANDLERS[int(choice)](lib, today)
            except LibraryError as err:
                print(f"ERROR [{err.label}]: {err}")
            except (EOFError, KeyboardInterrupt):
                raise
            except Exception as err:  # last line of defence: the menu must never crash
                print(f"Something went wrong: {err}")
            finally:
                print()
    except (EOFError, KeyboardInterrupt):
        print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # lets the rupee sign print on Windows
    today = get_today()
    db_path = os.environ.get("LIBRARY_DB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")
    if "--reset" in sys.argv and os.path.exists(db_path):     # start again from the starter data
        try:
            os.remove(db_path)
        except OSError as err:
            sys.exit(f"Could not delete {db_path}: {err}")
    try:
        lib = Library(Database(db_path))
        if lib.item_repo.count() == 0:                        # first run: fill the empty database
            lib.load_data(DATA_DIR)
        counts = lib.counts()
    except (OSError, KeyError, ValueError) as err:
        sys.exit(f"Could not open the database or data files: {err}")
    print(f"Loaded {counts['items']} items, {counts['members']} members, "
          f"{counts['loans']} loans, {counts['fines']} fines.")
    print(f"Today is {today}.\n")
    print(MENU)
    run_menu(lib, today)


if __name__ == "__main__":
    main()
