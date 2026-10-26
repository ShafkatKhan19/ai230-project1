"""Benchmarking harness: input generators, a careful timer, a comparison counter,
and a log-log slope fit.

Timing method
-------------
* time.perf_counter() (highest-resolution monotonic clock in Python).
* The garbage collector is switched off while a run is being timed, so a
  collection triggered by an unrelated allocation is not charged to the sort.
* Each measurement is repeated and the MEDIAN is reported, which is not thrown off by
  one-off interruptions by the operating system.
* The input is generated once per (size, input type); every repetition sorts
  the same list (the sorts copy their input, so the list is never modified).
"""

import gc
import math
import platform
import random
import statistics
import sys
import time

# --------------------------------------------------------------------------
# Input generators
# --------------------------------------------------------------------------

def random_ints(n, rng, k=None):
    """n integers drawn uniformly from [0, k); default k = 10n (few duplicates)."""
    k = k or 10 * max(n, 1)
    return [rng.randrange(k) for _ in range(n)]


def sorted_ints(n, rng):
    return sorted(random_ints(n, rng))


def reversed_ints(n, rng):
    return sorted(random_ints(n, rng), reverse=True)


def nearly_sorted_ints(n, rng, swap_fraction=0.01):
    """Sorted list with about 1% of positions swapped with a random partner."""
    a = sorted_ints(n, rng)
    for _ in range(max(1, int(n * swap_fraction))):
        i, j = rng.randrange(n), rng.randrange(n)
        a[i], a[j] = a[j], a[i]
    return a


def few_unique_ints(n, rng):
    """Only 10 distinct values: many duplicates."""
    return [rng.randrange(10) for _ in range(n)]


INPUT_TYPES = {
    "random": random_ints,
    "sorted": sorted_ints,
    "reversed": reversed_ints,
    "nearly_sorted": nearly_sorted_ints,
    "few_unique": few_unique_ints,
}

# --------------------------------------------------------------------------
# Timing
# --------------------------------------------------------------------------

def time_call(fn, *args, repeats=5):
    """Median wall-clock seconds of fn(*args) over `repeats` runs, GC disabled."""
    times = []
    for _ in range(repeats):
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            start = time.perf_counter()
            fn(*args)
            times.append(time.perf_counter() - start)
        finally:
            if gc_was_enabled:
                gc.enable()
    return statistics.median(times)


def time_many_calls(fn, args_list, repeats=5):
    """Median over `repeats` of the MEAN time per call across args_list.

    Used for searches: a single binary search takes well under a
    microsecond, below what one timer reading can resolve reliably, so we
    time a batch of queries and divide.
    """
    per_call = []
    for _ in range(repeats):
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            start = time.perf_counter()
            for args in args_list:
                fn(*args)
            per_call.append((time.perf_counter() - start) / len(args_list))
        finally:
            if gc_was_enabled:
                gc.enable()
    return statistics.median(per_call)

# --------------------------------------------------------------------------
# Counting comparisons (a machine-independent cost measure)
# --------------------------------------------------------------------------

class Counted:
    """Wraps a value and counts every `<` comparison made on it.

    All comparison sorts in this project only use `<`, so wrapping the input
    in Counted objects counts exactly the comparisons the algorithm makes.
    """
    comparisons = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        Counted.comparisons += 1
        return self.v < other.v


class ProbeList(list):
    """A list that records which positions are read by indexing (items[i]).

    len(probe_list.seen) is the number of DISTINCT elements a search looked
    at, a machine-independent cost (reading the same element twice is
    counted once). Iteration (for x in items) does not go through
    __getitem__, so linear search is not measured this way.
    """
    __slots__ = ("seen",)

    def __init__(self, *args):
        super().__init__(*args)
        self.seen = set()

    def __getitem__(self, i):
        self.seen.add(i)
        return super().__getitem__(i)


def count_comparisons(sort_fn, data):
    Counted.comparisons = 0
    result = sort_fn([Counted(x) for x in data])
    assert [c.v for c in result] == sorted(data), "sort produced a wrong result"
    return Counted.comparisons

# --------------------------------------------------------------------------
# Analysis helpers
# --------------------------------------------------------------------------

def loglog_slope(ns, ts):
    """Least-squares slope of log(t) against log(n).

    If t ~ c * n^p then the slope estimates p: about 1 for linear, about 2
    for quadratic, and a little above 1 (1.05-1.15 over typical ranges) for
    n log n.
    """
    xs = [math.log(n) for n in ns]
    ys = [math.log(t) for t in ts]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


def machine_info():
    import os
    cpu = platform.processor() or "unknown"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "cpu": cpu,
        "logical_cpus": os.cpu_count(),
    }


def make_rng(*keys):
    """A reproducible RNG for one experiment cell.

    Uses CRC32 rather than hash(): Python randomizes string hashes per
    process, so hash() would give different inputs on every run.
    """
    import zlib
    return random.Random(zlib.crc32(repr(("ai230",) + keys).encode()))
