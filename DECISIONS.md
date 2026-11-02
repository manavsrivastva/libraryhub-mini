# DECISIONS.md

## Phase 1

### D1. Which collections hold the data? (task 1.3)
- **Problem:** the engine needs fast lookup by ISBN and member ID, ordered history, and a uniqueness check.
- **Options:** everything in lists; dicts for lookups; a database now.
- **Chose:** `dict` by ISBN and by member ID (O(1) lookup), `list` of loans (history is ordered and is only appended to), `set` of ISBNs (R9 uniqueness check), `deque` per ISBN for the waiting list (first in, first out).
- **Why:** each structure matches how that data is used. Rejected a list of items because every lookup would scan it.

### D2. Where does fine calculation live?
- **Options:** `Member`, `Library`, or `Loan`.
- **Chose:** `Loan.fine(on_date, rate, price)`.
- **Why:** the loan owns the due date and the return date, so it can count the late days (R10). The member only supplies the rate and the item only supplies the price, passed in as numbers so `Loan` never has to store a member.
- **Against:** a bit awkward to pass rate and price in; but it keeps Loan independent and easy to test (the fine table tests use no Library).

### D3. Which fines count for R4?
- **Problem:** Rahul and Karthik both have overdue open loans with no fine saved yet.
- **Chose:** only saved, unpaid fines count (the rows in the fines list). Accruing "fine so far" is display-only.
- **Why:** the sample proves it: Karthik's ₹120 equals his two unpaid fine rows exactly, and his overdue loan L002 adds nothing.

### D4. What happens to a copy when a member is waiting? (R7)
- **Options:** only announce the next member; hold the copy for them; give it to them automatically.
- **Chose:** on return, the first member is removed from the queue and the copy is *held* for them. Only they can borrow it; anyone else gets "No copies ... available".
- **Why:** announcing alone lets a walk-in take the copy, which breaks "first person is served first".

### D5. Order of checks when renewing
- **Chose:** R2 (magazine) -> R6 renewed twice already -> R6 another member waiting.
- **Why:** R2 is a property of the item, so it is the cheapest and most basic check; the two R6 checks are not ranked by the Rulebook, so I check the member's own history before the queue.

### D6. How members are created from the CSV without `if member_type ==`
- **Chose:** a lookup dict `MEMBER_TYPES = {"Student": StudentMember, ...}` (and `ITEM_TYPES` for items). New membership types only need a new class.

## Phase 2

### D7. What does an undo-stack entry store?
- **Problem:** pushing only the `Loan` object is not enough to reverse an operation.
- **Options:** (a) store the Loan; (b) store a full copy of the whole library before each operation; (c) store a small snapshot of exactly what changed.
- **Chose:** (c). A *borrow* entry stores the loan and where the member sat in the held list (if the copy was held for them). A *return* entry stores the loan, the fine record that was created (or None), and who was taken off the front of the waiting list.
- **Why:** undoing a borrow must free the copy, remove the loan, give the loan number back and re-hold the copy. Undoing a return must reopen the loan, remove the fine (and the unpaid total), and put the notified member back at the FRONT of the queue (`appendleft`), or first come, first served would break. (b) works but wastes memory.

### D8. Waiting list as a `collections.deque`
- **Options:** list with `pop(0)`; `deque` with `popleft()`.
- **Chose:** `deque`. `list.pop(0)` shifts every remaining element (O(n)); `deque.popleft()` is O(1). Benchmark on 100,000 entries: see `benchmark_results.md` (about 250x on my test run).

### D9. Indexes added to Library
- **Problem:** Phase 1 scanned the loans list for every return, every limit check and every fine total.
- **Chose:** `loan_index` (dict by loan ID), `active` (member -> {isbn: loan}) and `_unpaid` (member -> total). All are updated in ONE place (`_register_loan`, `return_item`, `undo`).
- **Trade-off:** more memory and more places that must stay in sync, in exchange for O(1) borrow and return. The Phase 1 tests prove behaviour did not change.

### D10. Borrow history order
- **Chose:** ordered by *issue date* (loan ID as tie-break), inserted oldest to newest so the head is the newest. Sorting by ID would also work on the starter data but would be wrong if IDs are ever not in date order. The history includes returned loans; option 7 lists active loans only.

### D11. Menu range
- **Chose:** `MAX_OPTION = 9` as a constant and the "Please enter a number from 0 to N." message uses it, so the Phase 1 test now reads the constant instead of the literal 8. Behaviour for bad input is unchanged.

### D12. Audit trail and undo
- **Chose:** undo does NOT delete the original audit entry; it appends an `undo-borrow` / `undo-return` entry. An audit log is a record of what happened, so history is never rewritten.

## Phase 3 (Part A: design and SQL)

### D13. Is "available copies" stored in a column or calculated?
- **Stored** (`items.available_copies`): reading is instant; but every borrow, return, undo and cancelled transaction must update it, and two simultaneous borrows can both read "1", both decrement, and leave -1 or a wrong number. One forgotten UPDATE and the number lies forever.
- **Calculated** (`total_copies - COUNT(open loans)`, query Q11): always true, because the loans rows ARE the truth; nothing to keep in sync. Costs a count per read.
- **Chose: calculated.** It cannot drift. With the partial index on open loans the count is cheap.
- **I would denormalise** (store a counter, kept right by a trigger or by the borrow transaction) if reads vastly outnumbered writes at huge scale, for example the catalogue page of a 10-million-loan library, and I had measured the count as the bottleneck.

### D14. ON DELETE behaviour
- Loans and items use **RESTRICT**: history must survive; anonymise a member instead of deleting. CASCADE only where the child is meaningless alone (fine -> loan, link rows, waiting-list places). `audit_log` has no foreign keys. Full table in `NORMALISATION.md`.

### D15. R8 enforced in the database too
- **Chose:** a partial unique index `one_open_loan_per_title ON loans (member_id, isbn) WHERE return_date IS NULL`. Python checks R8 first (for the friendly message); the database is the safety net if two requests race.

### D16. Reference items in Q11
- The query reports the raw `total_copies - open loans` (so the Encyclopaedia shows 1) because that is the expected output. The *meaning* ("not borrowable") comes from `item_type = 'Reference'`, and the Python/menu layer shows "not borrowable". One query answers "copies on the shelf"; the rule R1 answers "may it leave".

### D17. Membership limits live in two places
- The Rulebook numbers are in the Python classes (Phase 1) AND in the `membership_types` table. For Part A the Python classes stay the source of truth for rules; Part B adds a test that the table and the classes agree, so they cannot drift silently.

### D18. SQLite, and how borrow is made atomic
- **Chose:** SQLite (built into Python; no installs). Borrow is one transaction opened with `BEGIN IMMEDIATE`, which takes the write lock before the availability check, so two people cannot both take the last copy. `PRAGMA foreign_keys = ON` is set on every connection because SQLite ignores foreign keys otherwise.

### D19. Next loan number
- `MAX(number) + 1` computed inside the transaction, not an auto-increment counter, so an undone borrow (a deleted row) gives its number back (matches the Phase 2 sample "loan L011 removed").

## Phase 3 (Part B: the engine on the database)

### D20. The .sql files are generated, never read
- **Problem:** on the company laptop Python was refused permission to OPEN `.sql` files (PowerShell could read them).
- **Options:** keep fighting the permission; keep a `.txt` copy; make the program independent of reading `.sql` at all.
- **Chose:** the schema (`sql_schema.py`) and the queries (`sql_queries.py`) are Python strings, which always load. `export_sql.py`
  WRITES `schema.sql`, `seed.sql` (from SQLite's own `iterdump`) and `queries.sql` for the hand-in. Tests compare the files with the
  Python sources only when the files are readable.
- **Why:** one source of truth, no runtime dependency on a blocked file type, and the hand-in files cannot drift (a test checks them).

### D21. Library talks only to repository classes
- `storage/` has `ItemRepository`, `MemberRepository`, `LoanRepository` (+ fines), `ReservationRepository` and `AuditRepository`, all with
  `?` placeholders. `Library` has no SQL in it. A test scans `library.py` and `storage/` for string-built SQL.
- The Phase 2 in-memory engine is kept as `phase2_library.py` ONLY for `benchmark.py`, so the Phase 2 measurements remain reproducible.

### D22. `@audit` now also means "one transaction"
- The decorator wraps the method in `db.transaction()` and inserts the audit row inside the same transaction. If any statement fails
  the loan AND the audit row are rolled back together (tested by making the audit insert fail).
- The undo snapshot is pushed only AFTER the commit, so a rolled-back operation can never be undone by mistake.

### D23. How the waiting list is stored
- `reservations(isbn, member_id, status, seq)`: `seq` is the queue position and `status` is `waiting` or `held`. A returned copy changes the
  first waiting row to `held` and KEEPS its `seq`, so undoing a return puts the member back in exactly their old place. Restarting the
  program loses nothing (tested).

### D24. "A fresh temporary database per test"
- `Library()` with no argument creates a private in-memory database, so every test starts from nothing and cannot see another test's data.
  Persistence tests use a real file in a temporary folder and close the connection first.

### D25. Start-up and `--reset`
- First run on an empty database loads the starter CSVs; later runs just open the file. `--reset` deletes the file first.
  The start-up line "Loaded N items, ..." now reports what is stored, so after a borrow it says 11 loans.

### D26. Whole-table views versus lookups
- `lib.items`, `lib.members`, `lib.loans`, `lib.fines`, `lib.audit_log` are computed read-only views kept so the Phase 1 and 2 tests and
  reports run unchanged on the database. The menu uses `get_item` / `get_member` (one row) instead, because building the whole table on every
  lookup would not scale to 10,000 titles.
