"""Short live demo for the project defense (runs in a few seconds).

    python demo.py
"""

import math
import random
import time

from complexity_lab.harness import ProbeList, count_comparisons
from complexity_lab.searching import binary_search, interpolation_search, linear_search
from complexity_lab.sorting import (insertion_sort, merge_sort, quick_sort_first,
                                    quick_sort_random)

rng = random.Random(1)
n = 2000
random_data = [rng.randrange(10 * n) for _ in range(n)]
sorted_data = sorted(random_data)

print(f"1) Comparisons made while sorting n = {n:,} numbers")
for name, fn in [("insertion", insertion_sort), ("merge", merge_sort),
                 ("quick (first pivot)", quick_sort_first), ("quick (random pivot)", quick_sort_random)]:
    print(f"   {name:<21} random input: {count_comparisons(fn, random_data):>9,}"
          f"   sorted input: {count_comparisons(fn, sorted_data):>9,}")
print(f"   for reference: n log2 n = {n * math.log2(n):,.0f}, n(n-1)/2 = {n * (n - 1) // 2:,}")

print("\n2) Time to sort the same sorted list")
for name, fn in [("quick (first pivot)", quick_sort_first), ("quick (random pivot)", quick_sort_random)]:
    start = time.perf_counter()
    fn(sorted_data)
    print(f"   {name:<21} {1e3 * (time.perf_counter() - start):8.2f} ms")

print("\n3) Searching a sorted list of 1,000,000 numbers for its last element")
big = list(range(1_000_000))
for name, fn in [("linear", linear_search), ("binary", binary_search)]:
    start = time.perf_counter()
    fn(big, 999_999)
    print(f"   {name:<14} {1e3 * (time.perf_counter() - start):8.3f} ms")

print("\n4) Elements examined by interpolation vs binary search (n = 10,000)")
even = list(range(0, 20_000, 2))
skewed = list(range(9_999)) + [10**15]
for label, items in [("evenly spread", even), ("one huge outlier", skewed)]:
    for name, fn in [("binary", binary_search), ("interpolation", interpolation_search)]:
        pl = ProbeList(items)
        fn(pl, items[9_000])
        print(f"   {label:<17} {name:<14} {len(pl.seen):>6,} elements")
