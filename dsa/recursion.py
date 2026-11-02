"""Recursion warm-ups. For each: base case, and how the problem gets smaller."""


def factorial(n):
    # Base case: 0! = 1.  Smaller problem: n! = n * (n-1)!
    if n == 0:
        return 1
    return n * factorial(n - 1)


def fibonacci(n):
    # Base cases: fib(0)=0, fib(1)=1.  Smaller problems: fib(n-1) and fib(n-2).
    # This version recomputes the same values again and again: about 2^n calls.
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_memo(n, cache=None):
    """Same idea, but each value is stored in a dict the first time: O(n) calls."""
    cache = {} if cache is None else cache
    if n < 2:
        return n
    if n not in cache:
        cache[n] = fibonacci_memo(n - 1, cache) + fibonacci_memo(n - 2, cache)
    return cache[n]


def sum_of_digits(n):
    # Base case: a single digit.  Smaller problem: drop the last digit (n // 10).
    if n < 10:
        return n
    return n % 10 + sum_of_digits(n // 10)


def factorial_iter(n):
    result = 1
    for k in range(2, n + 1):
        result *= k
    return result
