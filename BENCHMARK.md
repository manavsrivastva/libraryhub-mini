# Benchmark report (Phase 2): FILL THIS IN YOURSELF

Run `python benchmark.py` on your own laptop and paste its tables here.
The numbers will differ from anyone else's; the SHAPE is what matters.

## 1. Predictions (write these BEFORE you run the benchmark)
| Method | Predicted time | Predicted space | Why (one sentence) |
|---|---|---|---|
| list_items | | | |
| search | | | |
| borrow | | | |
| return_item | | | |
| overdue_report | | | |

## 2. Measured results
(paste the first table from benchmark_results.md)

For every row where prediction and measurement disagree, write TWO sentences: what you saw, and why.
Things to think about: a 10x bigger input should make an O(n) method about 10x slower. Is that what you
measured? (Memory caches and garbage collection often make big inputs slower than the Big-O alone says.)
Why does `borrow` stay flat while the library grows 50x? What would happen to `return_item` if `get_open_loan`
still scanned the list?

## 3. Sort comparison
(paste the second table)
- Which columns barely move when n doubles, which roughly double, which roughly quadruple? Name the Big-O of each.
- Why is `sorted()` so much faster than your hand sorts? (Hint: language it is written in, and its algorithm, Timsort.)
- After how many searches does "sort once, then binary search" beat plain linear search? (Sort cost / (linear cost - binary cost).)

## 4. list.pop(0) vs deque.popleft()
(paste the result) Why is `pop(0)` slow? What does a deque do differently inside?

## 5. Conclusions
Three to five sentences: which structure for which feature, and why.
