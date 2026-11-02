# LibraryHub Mini — Phase 4 Behaviour Table

**Test environment**
- Backend: FastAPI
- Frontend: React + Vite
- Database: `library_test.db`
- Test date: `2026-10-12`

## Behaviour checklist

| # | Action | Expected result | Status | Notes |
|---|---|---|---|---|
| 1 | Open `/` | Loading catalogue indicator, followed by 7 book cards | PARTIAL | Catalogue screen opened and screenshot captured; exact card count not recorded. |
| 2 | Type `py` | Only Python Crash Course appears; 1 result | NOT VERIFIED | Search implementation exists; exact sample result needs checking. |
| 3 | Type `zzz` | No-results message: "No items match 'zzz'. Try a different word." | PARTIAL | Empty-results screenshot reported as captured; exact message not reviewed. |
| 4 | Click a book card | URL changes to its details route and availability is displayed | PARTIAL | Book details and navigation were tested; exact sample ISBN and availability not recorded. |
| 5 | Open The Alchemist | 0 of 1 available; Join waiting list button | NOT VERIFIED | Availability exists in test data; exact UI behaviour not confirmed. |
| 6 | Open Encyclopaedia of Science | Reference-item message; no borrow button | PARTIAL | Reference-item borrowing failure was tested; absence of the borrow button was not separately confirmed. |
| 7 | Select Asha; add 3 items and try a 4th | Basket limit message; fourth button disabled | NOT VERIFIED | UI membership-limit behaviour still needs testing. |
| 8 | Borrow with a valid basket | Borrowing indicator and successful borrowing message | PASS | Successful borrowing and partial checkout were tested with Divya. |
| 9 | Return to catalogue after borrowing | Updated availability is displayed | NOT VERIFIED | Availability refresh after checkout needs testing. |
| 10 | Select Karthik and borrow Clean Code | Server message explains unpaid fines above the limit | NOT VERIFIED | Backend test data has Karthik's unpaid fines; exact frontend message needs checking. |
| 11 | Select Rahul and open My Loans | The Alchemist appears overdue by 20 days | PASS | Rahul's loan information and overdue status were tested. |
| 12 | Stop API and reload | Friendly server error and Retry button | PARTIAL | API-down error was tested; Retry-button behaviour needs confirmation. |
| 13 | Open `/nothing` | Friendly 404 page with link to catalogue | PASS | 404 page was tested. |
| 14 | Enter ISBN `123` in Add Item | Validation message; submit disabled | PASS | Add-book form validation was tested. |
| 15 | Submit valid Add Item form | Success message, cleared form and new catalogue item | PASS | The Learning Journey was successfully added in the test database. |

## Additional completion checks

| Requirement | Status | Notes |
|---|---|---|
| Loading state screenshot | NOT VERIFIED | Confirm the screenshot is saved locally. |
| Empty state screenshot | PARTIAL | Reported captured; contents not reviewed. |
| API error screenshot | NOT VERIFIED | Confirm the screenshot is saved locally. |
| Stale search response protection | NOT VERIFIED | AbortController and debounce are implemented; race-condition test not confirmed. |
| Responsive layout at 360px | NOT VERIFIED | Needs browser testing. |
| Keyboard accessibility | NOT VERIFIED | Needs keyboard-navigation testing. |
| All data-fetching screens handle loading, empty and error | NOT VERIFIED | Requires a screen-by-screen audit. |
| Back navigation preserves catalogue search state | NOT VERIFIED | Needs testing. |

## Status definitions

- **PASS:** The behaviour was explicitly tested and confirmed.
- **PARTIAL:** Some of the behaviour was tested, but the complete expected result was not confirmed.
- **NOT VERIFIED:** There is not enough test evidence to claim it works.

## Final note

This table records the verification evidence available so far. Items marked PARTIAL or NOT VERIFIED should not be presented as fully passing.

The test database was used to avoid modifying the original project database during Phase 4 testing.
