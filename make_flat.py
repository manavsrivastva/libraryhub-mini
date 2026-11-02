"""3.1: combine the starter CSVs into ONE flat file, one row per loan.   python make_flat.py"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(name):
    with open(os.path.join(HERE, "data", name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


books = {b["isbn"]: b for b in rows("books.csv")}
members = {m["member_id"]: m for m in rows("members.csv")}
fines = {f["loan_id"]: f for f in rows("fines.csv")}
columns = ["loan_id", "member_name", "email", "membership_type", "item_title", "authors", "isbn",
           "category", "parent_category", "pages", "price", "issue_date", "due_date", "return_date",
           "fine", "fine_paid"]
with open(os.path.join(HERE, "library_flat.csv"), "w", newline="", encoding="utf-8") as out:
    writer = csv.writer(out)
    writer.writerow(columns)
    for loan in rows("loans.csv"):
        m, b, f = members[loan["member_id"]], books[loan["isbn"]], fines.get(loan["loan_id"])
        writer.writerow([loan["loan_id"], m["name"], m["email"], m["membership_type"], b["title"],
                         b["authors"], b["isbn"], b["category"], b["parent_category"], b["pages"],
                         b["price"], loan["issue_date"], loan["due_date"], loan["return_date"],
                         f["amount"] if f else "", f["paid"] if f else ""])
print("Wrote library_flat.csv (10 rows).")
