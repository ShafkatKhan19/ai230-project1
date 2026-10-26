"""Run every experiment and write results/*.csv, results/machine.json and figures/*.png.

    python run_experiments.py            # full run
    python run_experiments.py --quick    # small sizes, for a fast check

Experiments
  E1 growth        time vs n on random input, every algorithm (+ Python's sorted as reference)
  E2 input_order   time at fixed n for 5 input orders (best/worst cases)
  E3 comparisons   comparison counts vs the textbook formulas
  E4 small_n       insertion vs merge for small n (constant factors / crossover)
  E5 counting_k    counting sort at fixed n as the value range k grows
  E6 search        time per query vs n for all four searches
  E7 linear_pos    linear search time vs position of the target
  E8 quick_details quicksort swaps per input order; comparisons with many duplicates
  E9 search_probes elements examined by binary, jump and interpolation search on 3 data shapes
"""

import argparse
import csv
import json
import math
import os
import sys

from complexity_lab import harness as H
from complexity_lab.searching import (SEARCHES, binary_search, interpolation_search,
                                      jump_search, linear_search)
from complexity_lab.sorting import (ALL_SORTS, counting_sort, insertion_sort,
                                    merge_sort)

QUADRATIC = {"insertion", "selection"}
RESULTS, FIGURES = "results", "figures"


def write_csv(name, rows):
    path = os.path.join(RESULTS, f"{name}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {path} ({len(rows)} rows)")


def log(msg):
    print(msg, flush=True)


def builtin_sorted(a):
    return sorted(a)


# --------------------------------------------------------------------------

def e1_growth(quick):
    sizes_fast = [2**k for k in range(8, 13 if quick else 18)]       # 256 .. 131072
    sizes_slow = [2**k for k in range(7, 10 if quick else 13)]       # 128 .. 4096
    algos = {**ALL_SORTS, "python_sorted": builtin_sorted}
    rows = []
    for name, fn in algos.items():
        sizes = sizes_slow if name in QUADRATIC else sizes_fast
        for n in sizes:
            data = H.random_ints(n, H.make_rng("e1", n))
            reps = 3 if n >= 32768 or name in QUADRATIC else 5
            t = H.time_call(fn, data, repeats=reps)
            rows.append({"algorithm": name, "n": n, "seconds": t, "repeats": reps})
        log(f"  E1 {name}: done up to n={sizes[-1]}")
    write_csv("e1_growth", rows)
    return rows


def e2_input_order(quick):
    n = 512 if quick else 2000
    rows = []
    for name, fn in {**ALL_SORTS, "python_sorted": builtin_sorted}.items():
        for kind, gen in H.INPUT_TYPES.items():
            data = gen(n, H.make_rng("e2", kind))
            t = H.time_call(fn, data, repeats=5)
            rows.append({"algorithm": name, "input": kind, "n": n, "seconds": t})
    log("  E2 done")
    write_csv("e2_input_order", rows)
    return rows


def e3_comparisons(quick):
    sizes = [2**k for k in range(6, 11 if quick else 14)]   # 64 .. 8192
    rows = []
    for name in ["insertion", "selection", "merge", "quick_first", "quick_random", "heap"]:
        for kind in ["random", "sorted"]:
            for n in sizes:
                if name in ("insertion", "selection", "quick_first") and n > 4096:
                    continue  # quadratic counts get slow to collect in pure Python
                data = H.INPUT_TYPES[kind](n, H.make_rng("e3", kind, n))
                c = H.count_comparisons(ALL_SORTS[name], data)
                rows.append({"algorithm": name, "input": kind, "n": n, "comparisons": c,
                             "n_log2_n": n * math.log2(n), "n2_over_2": n * (n - 1) / 2,
                             "n2_over_4": n * n / 4})
    log("  E3 done")
    write_csv("e3_comparisons", rows)
    return rows


def e4_small_n(quick):
    rows = []
    for n in [2, 4, 8, 16, 24, 32, 48, 64, 96, 128, 192, 256]:
        data = H.random_ints(n, H.make_rng("e4", n))
        reps = 21
        for name, fn in [("insertion", insertion_sort), ("merge", merge_sort)]:
            # many inner calls per sample so tiny n is measurable
            batch = [(data,)] * 200
            t = H.time_many_calls(fn, batch, repeats=reps)
            rows.append({"algorithm": name, "n": n, "seconds": t})
    log("  E4 done")
    write_csv("e4_small_n", rows)
    return rows


def e5_counting_k(quick):
    n = 10_000 if quick else 50_000
    rows = []
    for k in [10, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]:
        data = H.random_ints(n, H.make_rng("e5", k), k=k)
        t = H.time_call(counting_sort, data, repeats=3)
        rows.append({"n": n, "k": k, "seconds": t})
    log("  E5 done")
    write_csv("e5_counting_k", rows)
    return rows


def e6_search(quick):
    sizes = [2**k for k in range(8, 15 if quick else 21)]   # 256 .. ~1M
    rows = []
    for n in sizes:
        rng = H.make_rng("e6", n)
        items = list(range(0, 2 * n, 2))                     # sorted, distinct, even numbers
        queries = [(items, items[rng.randrange(n)]) for _ in range(200)]   # all present
        rows.append({"algorithm": "binary", "n": n,
                     "seconds_per_query": H.time_many_calls(binary_search, queries * 50, repeats=5)})
        rows.append({"algorithm": "interpolation", "n": n,
                     "seconds_per_query": H.time_many_calls(interpolation_search, queries * 50, repeats=5)})
        rows.append({"algorithm": "jump", "n": n,
                     "seconds_per_query": H.time_many_calls(jump_search, queries * 5, repeats=5)})
        lin_queries = queries[:20] if n >= 65536 else queries
        rows.append({"algorithm": "linear", "n": n,
                     "seconds_per_query": H.time_many_calls(linear_search, lin_queries, repeats=3)})
    log("  E6 done")
    write_csv("e6_search", rows)
    return rows


def e7_linear_position(quick):
    n = 100_000 if quick else 1_000_000
    items = list(range(n))
    rows = []
    for label, target in [("first", 0), ("quarter", n // 4), ("middle", n // 2),
                          ("last", n - 1), ("missing", -1)]:
        t = H.time_call(linear_search, items, target, repeats=5)
        rows.append({"position": label, "index": target, "n": n, "seconds": t})
    log("  E7 done")
    write_csv("e7_linear_position", rows)
    return rows


def e9_search_probes(quick):
    """Distinct elements examined per successful search, on three shapes of sorted data.

    even     n distinct values drawn uniformly from [0, 10n): what interpolation search assumes
    power    values i^4: smooth but far from evenly spread
    outlier  0, 1, ..., n-2 followed by one huge value: worst case for interpolation search
    """
    sizes = [2**k for k in range(8, 13 if quick else 17)]   # 256 .. 65,536
    shapes = {
        "even": lambda n, rng: sorted(rng.sample(range(10 * n), n)),
        "power": lambda n, rng: [i ** 4 for i in range(n)],
        "outlier": lambda n, rng: list(range(n - 1)) + [10**15],
    }
    rows = []
    for shape, make in shapes.items():
        for n in sizes:
            rng = H.make_rng("e9", shape, n)
            items = make(n, rng)
            targets = [items[rng.randrange(n - 1)] for _ in range(100)]   # present, not the outlier itself
            for name in ["binary", "jump", "interpolation"]:
                probes = []
                for t in targets:
                    pl = H.ProbeList(items)
                    assert items[SEARCHES[name](pl, t)] == t
                    probes.append(len(pl.seen))
                rows.append({"algorithm": name, "shape": shape, "n": n,
                             "mean_probes": sum(probes) / len(probes), "max_probes": max(probes)})
        log(f"  E9 {shape} done")
    write_csv("e9_search_probes", rows)
    return rows


def _counting_partition(counter):
    """Same logic as sorting._partition, plus a swap counter (used only in E8)."""
    def partition(a, lo, hi, pivot_index):
        a[pivot_index], a[hi] = a[hi], a[pivot_index]
        pivot = a[hi]
        i = lo
        for j in range(lo, hi):
            if a[j] < pivot:
                a[i], a[j] = a[j], a[i]
                counter["swaps"] += 1
                i += 1
        a[i], a[hi] = a[hi], a[i]
        return i
    return partition


def e8_quicksort_details(quick):
    """Swaps of first-pivot quicksort per input order, and comparisons of
    randomized quicksort on few-unique vs random input (same n and seeds as E2)."""
    from complexity_lab import sorting
    n = 512 if quick else 2000
    rows = []
    original = sorting._partition
    counter = {"swaps": 0}
    sorting._partition = _counting_partition(counter)
    try:
        for kind in ["random", "sorted", "reversed"]:
            data = H.INPUT_TYPES[kind](n, H.make_rng("e2", kind))
            counter["swaps"] = 0
            assert sorting.quick_sort_first(data) == sorted(data)
            rows.append({"measure": "quick_first_swaps", "input": kind, "n": n, "value": counter["swaps"]})
    finally:
        sorting._partition = original
    for kind in ["random", "few_unique"]:
        data = H.INPUT_TYPES[kind](n, H.make_rng("e2", kind))
        c = H.count_comparisons(sorting.quick_sort_random, data)
        rows.append({"measure": "quick_random_comparisons", "input": kind, "n": n, "value": c})
    log("  E8 done")
    write_csv("e8_quicksort_details", rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)
    info = H.machine_info()
    info["quick_mode"] = args.quick
    with open(os.path.join(RESULTS, "machine.json"), "w") as f:
        json.dump(info, f, indent=2)
    log(f"machine: {info}")
    for exp in [e1_growth, e2_input_order, e3_comparisons, e4_small_n,
                e5_counting_k, e6_search, e7_linear_position, e8_quicksort_details,
                e9_search_probes]:
        log(f"running {exp.__name__} ...")
        exp(args.quick)
    log("all experiments done; now run:  python make_figures.py")


if __name__ == "__main__":
    sys.exit(main())
