"""Replays the sample transcripts through the real menu loop."""
import builtins
from datetime import date

import main

TODAY = date(2026, 10, 12)


def run(lib, capsys, monkeypatch, lines):
    it = iter(lines)

    def fake_input(prompt=""):
        line = next(it, None)
        if line is None:
            raise EOFError            # input ran out, like Ctrl-D in a terminal
        print(prompt + line)          # a terminal would echo what the user typed
        return line

    monkeypatch.setattr(builtins, "input", fake_input)
    main.run_menu(lib, TODAY)
    return capsys.readouterr().out


def test_bad_menu_input_never_crashes(lib, capsys, monkeypatch):
    out = run(lib, capsys, monkeypatch, ["abc", "", "99", "0"])
    assert out.count(f"Please enter a number from 0 to {main.MAX_OPTION}.") == 3


def test_end_of_input_exits_cleanly(lib, capsys, monkeypatch):
    run(lib, capsys, monkeypatch, ["1"])       # no "0" at the end: EOF must not crash



def test_session_a_transcript(lib, capsys, monkeypatch):
    out = run(lib, capsys, monkeypatch, [
        "3", "M001", "9780000000011",
        "3", "M001", "9780000000011",
        "3", "M003", "9780000000066",
        "3", "M004", "9780000000035",
        "3", "M003", "9780000000028", "y",
        "4", "L001",
        "3", "M009",
        "3", "M001", "123",
        "3", "M001", "9780000000999",
        "0"])
    expected = """> 3
Member ID: M001
ISBN: 9780000000011
OK: Asha Raman borrowed 'Wings of Fire'. Due 2026-10-26.

> 3
Member ID: M001
ISBN: 9780000000011
ERROR [R8]: Asha Raman already has a copy of 'Wings of Fire'.

> 3
Member ID: M003
ISBN: 9780000000066
ERROR [R1]: 'Encyclopaedia of Science' is a reference item and cannot be borrowed.

> 3
Member ID: M004
ISBN: 9780000000035
ERROR [R4]: Karthik N has unpaid fines of ₹120 (limit ₹100).

> 3
Member ID: M003
ISBN: 9780000000028
No copies of 'The Alchemist' are available. Join waiting list? (y/n): y
OK: Sneha Iyer is #1 on the waiting list for 'The Alchemist'.

> 4
Loan ID: L001
OK: Rahul Mehta returned 'The Alchemist'. Late by 20 days. Fine: ₹100.
Next on waiting list: Sneha Iyer.

> 3
Member ID: M009
ERROR [MemberNotFoundError]: No member with ID M009.

> 3
Member ID: M001
ISBN: 123
ERROR [InvalidISBNError]: ISBN must be exactly 13 digits.

> 3
Member ID: M001
ISBN: 9780000000999
ERROR [ItemNotFoundError]: No item with ISBN 9780000000999.

> 0
"""
    assert out == expected


def test_member_loans_and_overdue_text(lib):
    assert main.format_member_loans(lib.member_loans("M002", TODAY)) == (
        "Loans for Rahul Mehta (Regular: 5 items, 21 days, ₹5/day)\n"
        "LOAN  TITLE          ISSUED      DUE         STATUS\n"
        "L001  The Alchemist  2026-09-01  2026-09-22  OVERDUE (20 days)\n"
        "Active loans: 1 of 5\n"
        "Unpaid fines: ₹0")
    assert main.format_overdue(lib.overdue_report(TODAY), TODAY) == (
        "Overdue loans as of 2026-10-12\n"
        "LOAN  MEMBER       TITLE                DUE         DAYS  FINE SO FAR\n"
        "L001  Rahul Mehta  The Alchemist        2026-09-22    20  ₹100\n"
        "L002  Karthik N    Python Crash Course  2026-10-05     7  ₹14\n"
        "Total overdue: 2   Fines so far: ₹114")


def test_return_on_time_message(lib, capsys, monkeypatch):
    out = run(lib, capsys, monkeypatch, ["4", "L003", "0"])
    assert "OK: Sneha Iyer returned 'Sapiens'. Returned on time. Fine: ₹0." in out
