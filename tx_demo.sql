-- 3.6 Transaction demo. Run against a freshly built database (python build_db.py).
-- before
SELECT COUNT(*) FROM loans WHERE loan_id = 'L011';   -- 0
SELECT COUNT(*) FROM audit_log;                      -- 0

-- attempt 1: the audit insert violates NOT NULL on purpose
BEGIN;
  INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date)
         VALUES ('L011', 'M001', '9780000000011', '2026-10-12', '2026-10-26');
  INSERT INTO audit_log (logged_at, action, member_id, isbn)
         VALUES ('2026-10-12', NULL, 'M001', '9780000000011');   -- ERROR: NOT NULL constraint failed
ROLLBACK;
SELECT COUNT(*) FROM loans WHERE loan_id = 'L011';   -- still 0

-- attempt 2: correct statements
BEGIN;
  INSERT INTO loans (loan_id, member_id, isbn, issue_date, due_date)
         VALUES ('L011', 'M001', '9780000000011', '2026-10-12', '2026-10-26');
  INSERT INTO audit_log (logged_at, action, member_id, isbn)
         VALUES ('2026-10-12', 'borrow', 'M001', '9780000000011');
COMMIT;
SELECT COUNT(*) FROM loans WHERE loan_id = 'L011';   -- 1
SELECT COUNT(*) FROM audit_log;                      -- 1
