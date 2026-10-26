"""Sorting algorithms implemented from scratch.

Every function takes a list and returns a NEW sorted list (ascending).
The input list is never modified, so the same input can be reused across
benchmark runs.

Predicted running times (n = number of elements, k = value range):

    insertion_sort        best O(n)        average O(n^2)     worst O(n^2)
    selection_sort        O(n^2) in every case
    merge_sort            O(n log n) in every case, O(n) extra space
    quick_sort_first      average O(n log n), worst O(n^2) (sorted input)
    quick_sort_random     expected O(n log n) on every input
    heap_sort             O(n log n) in every case, O(1) extra space
    counting_sort         O(n + k), integers only
    radix_sort            O(d * (n + b)), integers only (d digits in base b)
"""

import random


# --------------------------------------------------------------------------
# O(n^2) comparison sorts
# --------------------------------------------------------------------------

def insertion_sort(items):
    """Grow a sorted prefix; insert each new element by shifting larger ones right.

    Loop invariant: before iteration i, a[0:i] is sorted and holds the
    original first i elements.
    """
    a = list(items)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and key < a[j]:      # strict <, so equal keys keep their order (stable)
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def selection_sort(items):
    """Repeatedly select the minimum of the unsorted suffix and swap it into place.

    Always does n(n-1)/2 comparisons, whatever the input order.
    """
    a = list(items)
    n = len(a)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            if a[j] < a[smallest]:
                smallest = j
        a[i], a[smallest] = a[smallest], a[i]
    return a


# --------------------------------------------------------------------------
# O(n log n) comparison sorts
# --------------------------------------------------------------------------

def merge_sort(items):
    """Top-down merge sort. Recurrence T(n) = 2T(n/2) + Theta(n) -> Theta(n log n)."""
    a = list(items)
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    return _merge(merge_sort(a[:mid]), merge_sort(a[mid:]))


def _merge(left, right):
    """Merge two sorted lists into one sorted list (stable: ties go to `left`)."""
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if right[j] < left[i]:
            out.append(right[j])
            j += 1
        else:
            out.append(left[i])
            i += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def quick_sort_first(items):
    """Quicksort with the FIRST element as pivot (Lomuto partition, in place).

    On already-sorted input every partition is maximally unbalanced, so the
    recursion depth is n and the running time is Theta(n^2).  Recursion is
    done only on the smaller side, with a loop for the larger side, so the
    stack depth stays O(log n) even in that worst case.
    """
    a = list(items)
    _quick(a, 0, len(a) - 1, choose_pivot=lambda lo, hi: lo)
    return a


def quick_sort_random(items, seed=None):
    """Quicksort with a uniformly random pivot: expected O(n log n) on any input."""
    a = list(items)
    rng = random.Random(seed)
    _quick(a, 0, len(a) - 1, choose_pivot=lambda lo, hi: rng.randint(lo, hi))
    return a


def _quick(a, lo, hi, choose_pivot):
    while lo < hi:
        p = _partition(a, lo, hi, choose_pivot(lo, hi))
        # recurse on the smaller part, iterate on the larger part
        if p - lo < hi - p:
            _quick(a, lo, p - 1, choose_pivot)
            lo = p + 1
        else:
            _quick(a, p + 1, hi, choose_pivot)
            hi = p - 1


def _partition(a, lo, hi, pivot_index):
    """Lomuto partition. Returns the final index of the pivot.

    After the call: a[lo:p] < pivot <= a[p+1:hi+1].
    """
    a[pivot_index], a[hi] = a[hi], a[pivot_index]
    pivot = a[hi]
    i = lo
    for j in range(lo, hi):
        if a[j] < pivot:
            a[i], a[j] = a[j], a[i]
            i += 1
    a[i], a[hi] = a[hi], a[i]
    return i


def heap_sort(items):
    """Build a max-heap in O(n), then extract the maximum n times (O(log n) each)."""
    a = list(items)
    n = len(a)
    for start in range(n // 2 - 1, -1, -1):     # bottom-up heap construction
        _sift_down(a, start, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]              # move current max to its final place
        _sift_down(a, 0, end)
    return a


def _sift_down(a, root, size):
    """Restore the max-heap property for the subtree at `root` within a[0:size]."""
    while True:
        child = 2 * root + 1
        if child >= size:
            return
        if child + 1 < size and a[child] < a[child + 1]:
            child += 1                           # pick the larger child
        if a[root] < a[child]:
            a[root], a[child] = a[child], a[root]
            root = child
        else:
            return


# --------------------------------------------------------------------------
# Non-comparison sorts (integers only)
# --------------------------------------------------------------------------

COUNTING_SORT_MAX_RANGE = 10**7


def counting_sort(items, max_range=COUNTING_SORT_MAX_RANGE):
    """Count occurrences of each value in [min, max]. Time and space O(n + k), k = max - min + 1.

    The count array has k entries no matter how few items there are, so a
    3-element list spanning [0, 10^9] would need a billion counters.  Rather
    than exhaust memory, refuse ranges above `max_range`.
    """
    a = list(items)
    if not a:
        return a
    lo, hi = min(a), max(a)
    if hi - lo + 1 > max_range:
        raise ValueError(f"value range {hi - lo + 1:,} exceeds max_range={max_range:,}; use radix_sort")
    counts = [0] * (hi - lo + 1)
    for x in a:
        counts[x - lo] += 1
    out = []
    for offset, c in enumerate(counts):
        if c:
            out.extend([offset + lo] * c)
    return out


def radix_sort(items, base=256):
    """LSD radix sort: one stable bucket pass per base-`base` digit.

    Negative numbers are handled by sorting their absolute values separately
    and putting them, reversed, in front of the non-negatives.
    """
    a = list(items)
    negatives = [-x for x in a if x < 0]
    non_negatives = [x for x in a if x >= 0]
    return [-x for x in reversed(_radix_non_negative(negatives, base))] + \
        _radix_non_negative(non_negatives, base)


def _radix_non_negative(a, base):
    if not a:
        return a
    largest = max(a)
    place = 1
    while largest // place > 0:
        buckets = [[] for _ in range(base)]
        for x in a:
            buckets[(x // place) % base].append(x)   # appending keeps each pass stable
        a = [x for bucket in buckets for x in bucket]
        place *= base
    return a


# Registry used by the tests and the benchmark harness.
COMPARISON_SORTS = {
    "insertion": insertion_sort,
    "selection": selection_sort,
    "merge": merge_sort,
    "quick_first": quick_sort_first,
    "quick_random": quick_sort_random,
    "heap": heap_sort,
}
INTEGER_SORTS = {
    "counting": counting_sort,
    "radix": radix_sort,
}
ALL_SORTS = {**COMPARISON_SORTS, **INTEGER_SORTS}
