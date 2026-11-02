# 3.1 / 3.2: From one flat file to a proper database

`library_flat.csv` (made by `python make_flat.py`) has ONE ROW PER LOAN and every fact about the member,
the item and the fine repeated on it.

```
loan_id  member_name  email             membership_type  item_title           authors                           isbn           ... fine  fine_paid
L001     Rahul Mehta  rahul@example.com Regular          The Alchemist        Paulo Coelho                      9780000000028       
L004     Asha Raman   asha@example.com  Student          Wings of Fire        A.P.J. Abdul Kalam;Arun Tiwari    9780000000011
L007     Rahul Mehta  rahul@example.com Regular          Python Crash Course  Eric Matthes                      9780000000042
L008     Rahul Mehta  rahul@example.com Regular          Wings of Fire        A.P.J. Abdul Kalam;Arun Tiwari    9780000000011  40  yes
```

## Three anomalies (real rows)
| Anomaly | Example from the data | Why it hurts |
|---|---|---|
| **Update** | Rahul Mehta's email sits on rows L001, L007 and L008. Python Crash Course's price (₹700) sits on L002, L005 and L007. | Changing Rahul's email means editing 3 rows. Miss one and the file says two different things about the same person. |
| **Insert** | Divya Rao (M005) has never borrowed and the Encyclopaedia has never been lent. | There is no row to put them on: a row needs a `loan_id`, and inventing a fake loan would pollute every report. |
| **Delete** | L009 is the ONLY row mentioning *India Today (Oct 2026)*; L006 is the only row for *Clean Code*. | Deleting an old loan to "clean up" erases the magazine or the book itself (title, price, category). |

## 1NF: no repeating groups inside a cell
**What repeats inside a cell?** The `authors` column: `A.P.J. Abdul Kalam;Arun Tiwari` is two values in one cell.
A cell must hold one value, so Wings of Fire's loans (L004, L008, L010) each become two rows (one per author).

| Before (10 rows) | After 1NF (13 rows), key = (loan_id, author) |
|---|---|
| `L004 ... Wings of Fire, "A.P.J. Abdul Kalam;Arun Tiwari"` | `L004 ... Wings of Fire, A.P.J. Abdul Kalam` and `L004 ... Wings of Fire, Arun Tiwari` |

The cost is visible straight away: every member and item fact is now repeated even more.

## 2NF: every column depends on the WHOLE key
The key is now (loan_id, author). Which columns depend on only PART of it?
- member_name, email, membership_type, item_title, isbn, category, parent_category, pages, price,
  issue_date, due_date, return_date, fine, fine_paid depend on **loan_id alone** -> they move to `loans`.
- `author` depends on the **book** (isbn), not on a particular loan -> `item_authors (isbn, author)`.

Result: `loans(loan_id, member..., item..., dates, fine)` and `item_authors(isbn, author)`.

## 3NF: no column depends on a non-key column
- member_name, email and membership_type describe the **member**, not the loan (loan -> member -> details)
  -> `members`.
- title, category, parent_category, pages, price describe the **item** (loan -> isbn -> details) -> `items`.
- max items, loan days and fine per day depend on **membership_type** (Student -> 3, 14, ₹2) -> `membership_types`.
- parent_category depends on **category** (Programming -> Technology) -> `categories` with a self-reference.
- fine and fine_paid exist only for loans returned late; kept in their own `fines` table so `loans` has no
  mostly-empty columns.
- authors become an entity: `authors` + `item_authors` (many-to-many).

## Final tables (10)
`membership_types`, `members`, `categories` (self-reference via `parent_id`), `items`, `authors`,
`item_authors`, `loans`, `fines`, `reservations` (waiting list), `audit_log`.
See `schema.sql` and `er_diagram.dbml` (paste into dbdiagram.io).

### Cardinalities
- membership_types 1 : N members
- categories 1 : N categories (self), categories 1 : N items
- items N : M authors (through item_authors)
- members 1 : N loans; items 1 : N loans; loans 1 : 0..1 fines
- items 1 : N reservations; members 1 : N reservations

## ON DELETE choices (on purpose)
| Foreign key | Choice | Reason |
|---|---|---|
| loans.member_id -> members | **RESTRICT** | The library's history must survive. A member with loans cannot be deleted; to honour a privacy request, anonymise the member row instead. (CASCADE would silently erase loans AND fines, and the library's auditors would object.) |
| loans.isbn -> items | **RESTRICT** | Same: you cannot delete a title that has been lent. |
| fines.loan_id -> loans | CASCADE | A fine has no meaning without its loan. |
| item_authors -> items | CASCADE | The link row is meaningless without the book. |
| item_authors -> authors | RESTRICT | Do not lose an author that still has books. |
| reservations -> items / members | CASCADE | A waiting-list place for a deleted member or title is pointless. |
| members.membership_type -> membership_types | RESTRICT | Cannot delete a type that members still use. |
| audit_log | **no foreign keys** | An audit trail must outlive the things it describes. |
