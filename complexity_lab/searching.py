"""Searching algorithms implemented from scratch.

Each function returns the index of `target` in `items`, or -1 if it is not there.

    linear_search          O(n) worst case. Works on any list.
    binary_search          O(log n) worst case. List must be sorted.
    jump_search            O(sqrt n) worst case. List must be sorted.
    interpolation_search   O(log log n) on average for evenly spread numbers,
                           O(n) worst case. List must be sorted and numeric.
"""

import math


def linear_search(items, target):
    """Check every position from left to right."""
    for i, x in enumerate(items):
        if x == target:
            return i
    return -1


def binary_search(items, target):
    """Halve the search range each step.

    Invariant: if target is in items, its leftmost copy is in items[lo:hi].
    The range halves every iteration, so there are at most floor(log2 n) + 1
    iterations. Returns the leftmost index when there are duplicates.
    """
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    if lo < len(items) and items[lo] == target:
        return lo
    return -1


def jump_search(items, target):
    """Jump ahead in blocks of sqrt(n), then scan the one block that can hold target.

    At most about sqrt(n) jumps plus sqrt(n) steps in the block: O(sqrt n).
    Returns the leftmost index when there are duplicates.
    """
    n = len(items)
    if n == 0:
        return -1
    step = max(1, math.isqrt(n))
    prev = 0
    # jump while the last element of the current block is still smaller than target
    while prev + step < n and items[prev + step - 1] < target:
        prev += step
    for i in range(prev, min(prev + step, n)):
        if items[i] == target:
            return i
        if items[i] > target:
            return -1
    return -1


def interpolation_search(items, target):
    """Guess the position from the value, like looking up a name in a phone book.

    The probe is placed where target would be if the values were spread
    evenly between items[lo] and items[hi]. On evenly spread data this takes
    O(log log n) probes on average; on badly skewed data each probe can
    remove only one element, giving O(n). May return any matching index when
    there are duplicates.
    """
    lo, hi = 0, len(items) - 1
    while lo <= hi and items[lo] <= target <= items[hi]:
        if items[hi] == items[lo]:
            return lo if items[lo] == target else -1
        pos = lo + (target - items[lo]) * (hi - lo) // (items[hi] - items[lo])
        if items[pos] == target:
            return pos
        if items[pos] < target:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1


SEARCHES = {
    "linear": linear_search,
    "binary": binary_search,
    "jump": jump_search,
    "interpolation": interpolation_search,
}
