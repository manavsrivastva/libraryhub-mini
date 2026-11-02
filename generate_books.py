"""Generate fake books with valid ISBNs.   python generate_books.py 10000"""
import csv
import random
import sys

from items import Book

WORDS = ["Silent", "River", "Code", "Garden", "Empire", "Night", "Algorithm", "Journey", "Memory",
         "Storm", "Island", "Signal", "Harvest", "Mirror", "Compass", "Forest", "Legacy", "Orbit"]
FIRST = ["Asha", "Ravi", "Meera", "John", "Priya", "Omar", "Lena", "Arjun", "Sara", "Kiran"]
LAST = ["Rao", "Nair", "Smith", "Khan", "Iyer", "Patel", "Brown", "Das", "Mehta", "Joshi"]
CATEGORIES = [("Fiction", ""), ("History", ""), ("Biography", ""), ("Science", ""), ("Travel", ""),
              ("Programming", "Technology"), ("Software Engineering", "Technology")]


def generate_books(n, seed=42):
    rnd = random.Random(seed)            # same seed -> same books every run
    books = []
    for i in range(n):
        isbn = f"978{i + 1_000_000:010d}"            # 3 + 10 = 13 digits, unique, not in the starter data
        title = f"{rnd.choice(WORDS)} {rnd.choice(WORDS)} {i}"   # the number keeps titles unique
        authors = [f"{rnd.choice(FIRST)} {rnd.choice(LAST)}" for _ in range(rnd.choice([1, 1, 2]))]
        category, parent = rnd.choice(CATEGORIES)
        books.append(Book(isbn, title, authors, category, parent,
                          rnd.randint(80, 900), rnd.randint(100, 1500), rnd.randint(1, 5)))
    return books


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    books = generate_books(n)
    with open("generated_books.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["isbn", "title", "authors", "category", "parent_category", "item_type",
                    "pages", "price", "total_copies"])
        for b in books:
            w.writerow([b.isbn, b.title, ";".join(b.authors), b.category, b.parent_category or "",
                        "Book", b.pages, b.price, b.total_copies])
    from library import Library
    lib = Library()
    for b in books:
        lib.add_item(b)
    print(f"Generated {len(books)} books -> generated_books.csv, loaded {len(lib.items)} into a Library.")
