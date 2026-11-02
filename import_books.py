"""python import_books.py books_with_duplicate.csv"""
import sys

from dsa.hashing import import_books

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python import_books.py <books.csv>")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        items, messages, summary = import_books(sys.argv[1])
    except OSError as err:
        sys.exit(f"Could not read the file: {err}")
    for line in messages:
        print(line)
    print(summary)
