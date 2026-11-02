"""Three O(n^2) sorts written by hand, plus the catalogue sort used by the website later.

Each sort works on a COPY, prints the list after every pass when show=True, and returns
the sorted copy. `key` works like the key of sorted().
"""


def bubble_sort(values, key=lambda x: x, show=True):
    a = list(values)
    n = len(a)
    if show:
        print(f"bubble_sort({a})")
    for p in range(1, n):
        swapped = False
        for i in range(n - p):                  # the last p-1 items are already in place
            if key(a[i]) > key(a[i + 1]):
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        if show:
            print(f"  after pass {p}: {a}")
        if not swapped:                         # nothing moved: already sorted, stop early
            break
    return a


def insertion_sort(values, key=lambda x: x, show=True):
    a = list(values)
    if show:
        print(f"insertion_sort({a})")
    for i in range(1, len(a)):
        current = a[i]
        j = i - 1
        while j >= 0 and key(a[j]) > key(current):   # shift bigger items one step right
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = current
        if show:
            print(f"  after inserting index {i}: {a}")
    return a


def selection_sort(values, key=lambda x: x, show=True):
    a = list(values)
    if show:
        print(f"selection_sort({a})")
    for p in range(1, len(a)):
        smallest = p - 1
        for j in range(p, len(a)):
            if key(a[j]) < key(a[smallest]):
                smallest = j
        a[p - 1], a[smallest] = a[smallest], a[p - 1]
        if show:
            print(f"  after pass {p} (min={a[p - 1]}): {a}")
    return a


def catalogue_sort(items):
    """Top-level category ascending, then pages descending, then title ascending."""
    return sorted(items, key=lambda i: (i.top_category, -i.pages, i.title))


def format_catalogue_sort(items):
    rows = catalogue_sort(items)
    cat_w = max(len(i.top_category) for i in rows)
    title_w = max(len(i.title) for i in rows)
    page_w = max(len(str(i.pages)) for i in rows)
    return "\n".join(f"{i.top_category:<{cat_w}}  {i.title:<{title_w}}  {i.pages:>{page_w}}" for i in rows)
