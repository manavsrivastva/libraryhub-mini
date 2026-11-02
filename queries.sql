-- LibraryHub Mini: the 12-query pack.
-- Named parameter :today = '2026-10-12' is supplied by run_queries.py (never date('now'):
-- the samples need a fixed date).

-- Q1: Which books are in the category 'Biography', and who wrote them?
-- JOIN: INNER JOINs all the way. A book with no author or category would not belong in this answer.
SELECT i.title, a.name AS author
FROM items i
JOIN categories c    ON c.category_id = i.category_id
JOIN item_authors ia ON ia.isbn = i.isbn
JOIN authors a       ON a.author_id = ia.author_id
WHERE c.name = 'Biography'
ORDER BY i.title, ia.position;

-- Q2: Which items are on loan right now, and who has them?
-- JOIN: INNER JOIN: an open loan always has a member and an item (foreign keys guarantee it). "Not
-- returned" is IS NULL; "= NULL" would return nothing.
SELECT l.loan_id, m.name AS member, i.title
FROM loans l
JOIN members m ON m.member_id = l.member_id
JOIN items i   ON i.isbn = l.isbn
WHERE l.return_date IS NULL
ORDER BY l.loan_id;

-- Q3: Which open loans are overdue, and by how many days? (most overdue first)
-- JOIN: INNER JOIN, same reason as Q2. Overdue = still open AND due before today (R10: due day is not
-- late).
SELECT m.name AS member, i.title, l.due_date,
       CAST(julianday(:today) - julianday(l.due_date) AS INTEGER) AS days_overdue
FROM loans l
JOIN members m ON m.member_id = l.member_id
JOIN items i   ON i.isbn = l.isbn
WHERE l.return_date IS NULL AND l.due_date < :today
ORDER BY days_overdue DESC;

-- Q4: What are the 3 most borrowed titles? (ties broken by title)
-- JOIN: INNER JOIN loans -> items; titles with no loans are not in a "top" list anyway.
SELECT i.title, COUNT(*) AS loans
FROM loans l
JOIN items i ON i.isbn = l.isbn
GROUP BY i.isbn
ORDER BY loans DESC, i.title
LIMIT 3;

-- Q5: Which items have never been borrowed?
-- JOIN: LEFT JOIN keeps every item, including those with no loan rows; the loan columns are then NULL, and
-- WHERE l.loan_id IS NULL keeps exactly those. (An INNER JOIN would drop the very rows we want.)
SELECT i.title
FROM items i
LEFT JOIN loans l ON l.isbn = i.isbn
WHERE l.loan_id IS NULL;

-- Q6: Which members have had no loan in the last 90 days?
-- JOIN: none, NOT EXISTS (an anti-join). A LEFT JOIN with a date filter in ON would also work but is easier
-- to get wrong.
SELECT m.name
FROM members m
WHERE NOT EXISTS (
    SELECT 1 FROM loans l
    WHERE l.member_id = m.member_id AND l.issue_date >= date(:today, '-90 days')
);

-- Q7: Total fines per membership type per month (month the item was returned)?
-- JOIN: INNER JOINs fines -> loans -> members: only loans that HAVE a fine matter here.
SELECT m.membership_type, substr(l.return_date, 1, 7) AS month, SUM(f.amount) AS total_fines
FROM fines f
JOIN loans l   ON l.loan_id = f.loan_id
JOIN members m ON m.member_id = l.member_id
GROUP BY m.membership_type, month
ORDER BY m.membership_type, month;

-- Q8: How much in fines is paid versus pending?
-- JOIN: none, one table. paid is stored as 0/1, so CASE turns it into a readable label.
SELECT CASE paid WHEN 1 THEN 'Paid' ELSE 'Pending' END AS status, SUM(amount) AS total
FROM fines
GROUP BY paid
ORDER BY paid DESC;

-- Q9: Which members have borrowed from at least 3 different categories?
-- JOIN: INNER JOINs; COUNT(DISTINCT ...) because a member may borrow from one category many times.
SELECT m.name, COUNT(DISTINCT i.category_id) AS categories
FROM members m
JOIN loans l ON l.member_id = m.member_id
JOIN items i ON i.isbn = l.isbn
GROUP BY m.member_id
HAVING COUNT(DISTINCT i.category_id) >= 3
ORDER BY m.name;

-- Q10: In which categories does the average (returned) loan last more than 25 days?
-- JOIN: INNER JOINs. Open loans are excluded (no return date yet). HAVING filters AFTER averaging; WHERE
-- cannot.
SELECT c.name AS category,
       ROUND(AVG(julianday(l.return_date) - julianday(l.issue_date)), 1) AS avg_days
FROM loans l
JOIN items i      ON i.isbn = l.isbn
JOIN categories c ON c.category_id = i.category_id
WHERE l.return_date IS NOT NULL
GROUP BY c.category_id
HAVING AVG(julianday(l.return_date) - julianday(l.issue_date)) > 25
ORDER BY avg_days DESC;

-- Q11: How many copies of each title are available right now?
-- JOIN: LEFT JOIN, so titles with zero open loans still appear. The "still open" test is in ON, not WHERE:
-- in WHERE it would turn the LEFT JOIN back into an INNER JOIN and hide fully available titles. Reference
-- items show their raw copy count here (1) because nobody can borrow them; the app shows "not borrowable".
SELECT i.title, i.total_copies - COUNT(l.loan_id) AS available
FROM items i
LEFT JOIN loans l ON l.isbn = i.isbn AND l.return_date IS NULL
GROUP BY i.isbn
ORDER BY i.isbn;

-- Q12: Which pair of titles is most often borrowed by the same member?
-- JOIN: SELF JOIN of loans on member_id; a.title < b.title makes each pair appear once (no mirror, no title
-- with itself). COUNT(DISTINCT member) counts members, not loans.
SELECT a.title AS title_a, b.title AS title_b, COUNT(DISTINCT la.member_id) AS members
FROM loans la
JOIN loans lb ON lb.member_id = la.member_id
JOIN items a  ON a.isbn = la.isbn
JOIN items b  ON b.isbn = lb.isbn
WHERE a.title < b.title
GROUP BY a.isbn, b.isbn
ORDER BY members DESC, a.title, b.title
LIMIT 1;
