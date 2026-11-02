"""Hashing: sets and dicts give O(1) membership and lookup."""
import csv
import re
from collections import Counter, defaultdict

from errors import LibraryError
from items import ITEM_TYPES


def import_books(path):
    """Read a books CSV, skipping repeated ISBNs. Returns (items, messages, summary_line)."""
    seen = set()            # set: "have I met this ISBN?" in O(1)
    first_title = {}        # dict: which title used it first (for the message)
    items, messages = [], []
    rows = duplicates = invalid = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            line_no = reader.line_num          # header is line 1, first data row is line 2
            isbn = row["isbn"].strip()
            if isbn in seen:
                duplicates += 1
                messages.append(f"Line {line_no}: duplicate ISBN {isbn} "
                                f"(already used by '{first_title[isbn]}'), skipped.")
                continue
            try:
                item = ITEM_TYPES[row["item_type"]](
                    isbn, row["title"], row["authors"].split(";"), row["category"],
                    row["parent_category"], row["pages"], row["price"], row["total_copies"])
            except (LibraryError, ValueError, KeyError) as err:
                invalid += 1
                messages.append(f"Line {line_no}: {err}, skipped.")
                continue
            seen.add(isbn)
            first_title[isbn] = item.title
            items.append(item)
    summary = f"Imported {rows} rows: {len(items)} added, {duplicates} duplicate{'s' if duplicates != 1 else ''} skipped"
    if invalid:
        summary += f", {invalid} invalid skipped"
    return items, messages, summary + "."


def group_by_author(items):
    """dict: author -> sorted list of titles."""
    grouped = defaultdict(list)
    for item in items:
        for author in item.authors:
            grouped[author].append(item.title)
    return {author: sorted(grouped[author]) for author in sorted(grouped)}


def format_group_by_author(items):
    return "\n".join(f"{a}: {', '.join(t)}" for a, t in group_by_author(items).items())


def most_borrowed(loans, items_by_isbn, n=3):
    """Frequency counting. Ties are broken alphabetically by title."""
    counts = Counter(loan.isbn for loan in loans)
    ranked = sorted(((items_by_isbn[isbn].title, c) for isbn, c in counts.items()),
                    key=lambda pair: (-pair[1], pair[0]))
    return ranked[:n]


def format_most_borrowed(ranked):
    width = max(len(title) for title, _ in ranked)
    return "\n".join(f"{i}. {title:<{width}}  {count}" for i, (title, count) in enumerate(ranked, 1))


def reading_challenge(items, target_pages):
    """Two-sum in ONE pass with a dict. Reference items are excluded. Returns (a, b) or None."""
    seen = {}                                   # pages -> item already passed
    for item in items:
        if not item.is_borrowable():
            continue
        partner = seen.get(target_pages - item.pages)
        if partner is not None:
            return partner, item
        seen[item.pages] = item
    return None


def format_reading_challenge(items, target_pages):
    pair = reading_challenge(items, target_pages)
    if pair is None:
        return "No pair found."
    a, b = pair
    return f"{a.title} ({a.pages}) + {b.title} ({b.pages}) = {target_pages}"


def build_word_index(items):
    """Stretch: word -> set of ISBNs, for instant multi-word search."""
    index = defaultdict(set)
    for item in items:
        for word in re.findall(r"[a-z0-9]+", (item.title + " " + " ".join(item.authors)).lower()):
            index[word].add(item.isbn)
    return index


def search_index(index, query):
    """Every word must match (set intersection). Returns a sorted list of ISBNs."""
    words = re.findall(r"[a-z0-9]+", query.lower())
    if not words:
        return []
    result = set(index.get(words[0], set()))
    for word in words[1:]:
        result &= index.get(word, set())
    return sorted(result)
