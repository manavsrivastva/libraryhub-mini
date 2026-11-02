"""Searching: linear search (any list) and binary search (sorted list only)."""


def linear_search(seq, target, key=lambda x: x):
    """Return the index of the first element whose key equals target, else -1. O(n)."""
    for index, element in enumerate(seq):
        if key(element) == target:
            return index
    return -1


def linear_search_title(items, title):
    """Case-insensitive search by title over a list of items."""
    return linear_search(items, title.strip().lower(), key=lambda item: item.title.lower())


def binary_search_counted(sorted_seq, target, key=lambda x: x):
    """Return (index, comparisons). The list MUST already be sorted by `key`. O(log n).

    One comparison is counted per loop round (each round looks at one middle element).
    """
    low, high, comparisons = 0, len(sorted_seq) - 1, 0
    while low <= high:
        mid = (low + high) // 2
        comparisons += 1
        value = key(sorted_seq[mid])
        if value == target:
            return mid, comparisons
        if value < target:
            low = mid + 1      # target can only be in the right half
        else:
            high = mid - 1     # target can only be in the left half
    return -1, comparisons


def binary_search(sorted_seq, target, key=lambda x: x):
    return binary_search_counted(sorted_seq, target, key)[0]
