# LibraryHub Mini

LibraryHub Mini is a library management project developed in four phases:

1. Python and Object-Oriented Programming console engine
2. Data Structures and Algorithms
3. SQL and SQLite database integration
4. FastAPI backend and React frontend

---

## Project structure

```text
libraryhub/
├── api/                  # FastAPI application
├── data/                 # Starter CSV data
├── dsa/                  # Data Structures and Algorithms
├── storage/              # SQLite database layer
├── tests/                # Automated tests
├── web/                  # React + Vite frontend
├── errors.py
├── items.py
├── members.py
├── loans.py
├── library.py            # Core library business rules
├── main.py               # Console application
├── library.db            # SQLite database
├── requirements.txt
├── run_tests.py
├── build_db.py
├── schema.sql
├── seed.sql
├── queries.sql
├── NORMALISATION.md
├── DECISIONS.md
└── README.md
```

---

# Phase 1 — Python and OOP console engine

## Setup

From the project root:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Run the console application with a fixed sample date:

```powershell
$env:TODAY = "2026-10-12"
python main.py
```

Run tests:

```powershell
pytest
```

If the rupee symbol displays incorrectly in Windows:

```powershell
chcp 65001
```

## Main files

- `errors.py` — custom exceptions
- `items.py` — Book, Magazine and ReferenceItem
- `members.py` — Student, Regular and Premium
- `loans.py` — Loan model
- `library.py` — business rules, reports, audit decorator and generator
- `main.py` — console menu
- `data/` — starter CSV files

## Rule-to-test mapping

| Rule | Enforced by | Test |
|---|---|---|
| R1 Reference items cannot be borrowed | `ReferenceItem.is_borrowable`, `Library.borrow` | `test_r1_reference_item_cannot_be_borrowed` |
| R2 Magazine loan period and renewal | `Magazine.loan_days/can_renew`, `Library.renew` | `test_due_date_table`, `test_r2_magazine_cannot_be_renewed` |
| R3 Borrowing limit | `Member.max_items`, `Library.borrow` | `test_r3_borrow_limit` |
| R4 Unpaid fines above ₹100 | `Library.unpaid_fines`, `Library.borrow` | `test_r4_unpaid_fines_block`, `test_r4_boundary_exactly_100_is_allowed` |
| R5 Fine capped at item price | `Loan.fine` | `test_fine_table`, `test_r5_fine_saved_on_return_and_capped` |
| R6 Renewal rules | `Library.renew` | `test_r6_renewal_adds_loan_period_and_stops_at_two`, `test_r6_waiting_list_blocks_renewal` |
| R7 Waiting list | `Library.reserve`, `Library.return_item` | `test_r7_waiting_list_is_first_come_first_served` |
| R8 One copy per title per member | `Library.borrow`, `Library.reserve` | `test_r8_duplicate_title` |
| R9 ISBN validation and uniqueness | `LibraryItem.isbn`, `Library.add_item` | `test_r9_isbn_must_be_13_digits`, `test_r9_isbn_is_unique` |
| R10 Returning on due date is not late | `Loan.days_late` | `test_r10_returning_on_due_date_is_not_late`, `test_fine_table` |

---

# Phase 2 — Data Structures and Algorithms

No additional installations are required.

```powershell
python run_tests.py
python demo_phase2.py
python import_books.py books_with_duplicate.csv
python generate_books.py 10000
python benchmark.py
```

For a shorter benchmark:

```powershell
python benchmark.py --quick
```

The `dsa/` directory contains:

- `search.py`
- `sorting.py`
- `hashing.py`
- `history.py`
- `categories.py`
- `recursion.py`

Menu option 9 undoes the latest borrow or return.

---

# Phase 3 — SQL and SQLite

SQLite is included with Python.

## Useful commands

```powershell
python check_env.py
python run_tests.py
python build_db.py
python run_queries.py
python tx_demo.py
python injection_unsafe_demo.py
python index_experiment.py
python export_sql.py
```

Run the console application:

```powershell
python main.py
```

Reset the database to starter data:

```powershell
python main.py --reset
```

## Database configuration

By default, the database is `library.db` in the project root.

To use another database:

```powershell
$env:LIBRARY_DB = "C:\path\library.db"
```

The application architecture is:

```text
main.py
   |
library.py
   |
storage/
   |
SQLite
```

The `storage/` layer is responsible for SQL operations and uses parameterized queries.

The SQL hand-in files are:

- `schema.sql`
- `seed.sql`
- `queries.sql`

They are generated using `export_sql.py`.

Additional documentation:

- `NORMALISATION.md`
- `er_diagram.dbml`
- `BENCHMARK.md`

---

# Phase 4 — FastAPI and React frontend

Phase 4 adds a REST API and a browser-based interface to the existing library engine.

## Technologies

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| API server | Uvicorn |
| Database | SQLite |
| Frontend | React |
| Build tool | Vite |
| UI components | Material UI (MUI) |
| Routing | React Router |
| Frontend state | React Context API and useReducer |

## Prerequisites

- Python installed
- Node.js and npm installed
- Project dependencies installed

## Backend setup

Open a PowerShell terminal in the project root:

```powershell
cd C:\Users\manav_s\Desktop\MiniProject\libraryhub
```

Activate the Python virtual environment:

```powershell
venv\Scripts\activate
```

Install Python dependencies if necessary:

```powershell
pip install -r requirements.txt
```

Start the API:

```powershell
$env:TODAY = "2026-10-12"
python -m uvicorn api.main:app --reload
```

The API runs at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Keep this terminal running.

### Backend environment variables

| Variable | Purpose | Default |
|---|---|---|
| `LIBRARY_DB` | SQLite database path | Project root `library.db` |
| `TODAY` | Fixed date for loan and fine calculations | Current system date |
| `FRONTEND_ORIGIN` | Allowed frontend origin for CORS | `http://localhost:5173` |

For testing with a separate database, set `LIBRARY_DB` before starting the API:

```powershell
$env:LIBRARY_DB = "$PWD\library_test.db"
```

Use the intended database deliberately. The default is the main `library.db`.

## Frontend setup

Open a second PowerShell terminal:

```powershell
cd C:\Users\manav_s\Desktop\MiniProject\libraryhub\web
```

Install frontend dependencies:

```powershell
npm install
```

The frontend API configuration is stored in `web/.env`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the React development server:

```powershell
npm run dev
```

Open the local URL printed by Vite, normally:

```text
http://localhost:5173
```

Keep both backend and frontend terminals running while using the application.

## Frontend commands

Run from the `web/` directory:

```powershell
npm run dev
npm run build
npm run lint
npm run preview
```

- `dev` — starts the Vite development server.
- `build` — creates a production build.
- `lint` — runs ESLint.
- `preview` — previews the production build.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | API health check |
| GET | `/books` | List and search books |
| GET | `/books/{isbn}` | Get book details |
| POST | `/books` | Add a book |
| POST | `/reservations` | Reserve a book |
| POST | `/loans` | Borrow a book |
| POST | `/loans/{loan_id}/return` | Return a borrowed item |
| GET | `/members/{member_id}/loans` | Get member loan details |
| GET | `/members/{member_id}/reservations/{isbn}` | Get reservation status |

The API uses the existing `Library` business logic and SQLite storage layer.

Library errors are translated into HTTP responses with a JSON structure containing an error code and message.

## Frontend screens

The React application includes:

| Screen | Route | Purpose |
|---|---|---|
| Catalogue | `/` | Search, filter and sort books |
| Book details | `/books/:isbn` | View book information and availability |
| My loans | `/me` | View member loans and fines |
| Borrow basket | `/basket` | Manage basket and checkout |
| Add item | `/admin/add` | Add a library item |
| Not found | Other paths | Friendly 404 page |

## Frontend component structure

The application uses reusable components:

- `Navbar`
- `Layout`
- `BookCard`
- `BookList`
- `AvailabilityBadge`

Context providers manage the selected member and borrowing basket.

The basket uses a reducer to manage actions such as adding, removing and clearing items.

---

# Testing and verification

Run the backend tests from the project root:

```powershell
pytest
```

Or run the combined phase test runner:

```powershell
python run_tests.py
```

For Phase 4, start the API and frontend in separate terminals and verify the application against the intended SQLite database.

Check the following:

- Catalogue search, filtering and sorting
- Book details and availability
- Member loan information
- Waiting-list status
- Basket add, remove and clear
- Borrowing and server-side validation
- Add-item form validation and submission
- Loading, empty and error states
- Navigation and responsive layout

See the submission behaviour table for the actual verification status of each scenario.

---

# Design documentation

- `DECISIONS.md` — technical decisions and trade-offs
- `NORMALISATION.md` — database normalisation
- `er_diagram.dbml` — database entity relationship diagram
- `BENCHMARK.md` — performance experiment notes

