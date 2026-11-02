-- LibraryHub Mini: schema (SQLite). Every connection must run:  PRAGMA foreign_keys = ON;
-- (SQLite ignores foreign keys unless you switch them on, per connection.)

CREATE TABLE membership_types (
    type_name     TEXT    PRIMARY KEY,                       -- 'Student', 'Regular', 'Premium'
    max_items     INTEGER NOT NULL CHECK (max_items > 0),    -- R3
    loan_days     INTEGER NOT NULL CHECK (loan_days > 0),
    fine_per_day  INTEGER NOT NULL CHECK (fine_per_day >= 0) -- R5
);

CREATE TABLE members (
    member_id        TEXT PRIMARY KEY,
    name             TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email            TEXT NOT NULL UNIQUE CHECK (email LIKE '%@%'),
    membership_type  TEXT NOT NULL
        REFERENCES membership_types (type_name) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Self-referencing: Programming -> Technology. parent_id IS NULL means top level.
CREATE TABLE categories (
    category_id  INTEGER PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    parent_id    INTEGER REFERENCES categories (category_id) ON DELETE RESTRICT
);

CREATE TABLE items (
    isbn          TEXT PRIMARY KEY                             -- R9: exactly 13 digits, unique
        CHECK (length(isbn) = 13 AND isbn NOT GLOB '*[^0-9]*'),
    title         TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    category_id   INTEGER NOT NULL REFERENCES categories (category_id) ON DELETE RESTRICT,
    item_type     TEXT    NOT NULL CHECK (item_type IN ('Book', 'Magazine', 'Reference')),
    pages         INTEGER NOT NULL CHECK (pages > 0),
    price         INTEGER NOT NULL CHECK (price >= 0),
    total_copies  INTEGER NOT NULL CHECK (total_copies >= 0)
);

CREATE TABLE authors (
    author_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE
);

-- Many-to-many: a book has many authors, an author has many books.
CREATE TABLE item_authors (
    isbn       TEXT    NOT NULL REFERENCES items (isbn)      ON DELETE CASCADE,
    author_id  INTEGER NOT NULL REFERENCES authors (author_id) ON DELETE RESTRICT,
    position   INTEGER NOT NULL DEFAULT 1,                   -- keeps the order of the author list
    PRIMARY KEY (isbn, author_id)
);

CREATE TABLE loans (
    loan_id      TEXT PRIMARY KEY,
    member_id    TEXT    NOT NULL REFERENCES members (member_id) ON DELETE RESTRICT,
    isbn         TEXT    NOT NULL REFERENCES items (isbn)        ON DELETE RESTRICT,
    issue_date   TEXT    NOT NULL,                           -- YYYY-MM-DD
    due_date     TEXT    NOT NULL,
    return_date  TEXT,                                       -- NULL = not returned yet
    renewals     INTEGER NOT NULL DEFAULT 0 CHECK (renewals BETWEEN 0 AND 2),   -- R6
    CHECK (due_date >= issue_date),
    CHECK (return_date IS NULL OR return_date >= issue_date)
);

-- R8 in the database: a member can have only ONE OPEN loan per title.
-- (A partial unique index: returned loans are not part of it, so history can repeat.)
CREATE UNIQUE INDEX one_open_loan_per_title ON loans (member_id, isbn) WHERE return_date IS NULL;

-- A fine belongs to exactly one loan, and only loans that were returned late have one.
CREATE TABLE fines (
    loan_id  TEXT    PRIMARY KEY REFERENCES loans (loan_id) ON DELETE CASCADE,
    amount   INTEGER NOT NULL CHECK (amount >= 0),
    paid     INTEGER NOT NULL DEFAULT 0 CHECK (paid IN (0, 1))
);

-- The waiting list (R7). `seq` is the queue position: lower = served first. 'held' = a returned copy is
-- being kept for that member. Keeping the seq when a row goes waiting -> held makes undo exact.
CREATE TABLE reservations (
    reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn            TEXT NOT NULL REFERENCES items (isbn)      ON DELETE CASCADE,
    member_id       TEXT NOT NULL REFERENCES members (member_id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'held')),
    seq             INTEGER NOT NULL,
    UNIQUE (isbn, member_id)
);

-- Deliberately NO foreign keys: an audit trail must survive even if a member or item is removed.
CREATE TABLE audit_log (
    audit_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at  TEXT NOT NULL,
    action     TEXT NOT NULL,
    member_id  TEXT NOT NULL,
    isbn       TEXT NOT NULL
);
