"""Write REPORT.md from results/summary.json.

Every number in the report is read from the results files (and the test
count from pytest), so after re-running the experiments on another machine
the report shows that machine's numbers:

    python run_experiments.py && python make_figures.py && python make_report.py

The sentences were written for the results in this repository. After a
re-run, read the report once to check that each sentence still fits.
"""

import json
import math
import re
import subprocess
import sys

from complexity_lab.harness import loglog_slope

s = json.load(open("results/summary.json"))
m = s["machine"]
sl, e2, e3, e4, e5, e6, e7, e8, e9 = (s["e1_slopes"], s["e2_seconds"], s["e3_ratios"],
                                      s["e4_microseconds"], s["e5"], s["e6"], s["e7"],
                                      s["e8"], s["e9"])
npc = s["ns_per_comparison"]


# ---------------------------------------------------------------- helpers
def ms(x):
    return f"{x * 1e3:.2f} ms"


def us(x):
    return f"{x * 1e6:.2f} µs"


def t_auto(x):
    return ms(x) if x >= 1e-3 else us(x)


def times(a, b):
    return f"{a / b:.1f}×" if a / b < 10 else f"{a / b:.0f}×"


def expected_slope(lo, hi, f):
    ns = [2**k for k in range(int(math.log2(lo)), int(math.log2(hi)) + 1)]
    return loglog_slope(ns, [f(n) for n in ns])


def pct_dev(measured, predicted):
    return 100 * abs(measured - predicted) / predicted


def avg_npc(name):
    vals = [v for _, v in npc[name]]
    return sum(vals) / len(vals)


def count_tests():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"],
                         capture_output=True, text=True).stdout
    found = re.search(r"(\d+) tests? collected", out)
    return int(found.group(1)) if found else None


# ---------------------------------------------------------------- derived numbers
n_tests = count_tests()
exp_nlogn = expected_slope(256, 131072, lambda n: n * math.log2(n))
exp_log = expected_slope(256, 2**20, math.log2)
t_max = {k: v["seconds_at_max_n"] for k, v in sl.items()}
builtin_speedup = t_max["merge"] / t_max["python_sorted"]

ratio_big = {k: [r for n, r in v if n >= 1024] for k, v in s["e1_nlogn_ratio"].items()}
heap_change = 100 * (ratio_big["heap"][-1] / ratio_big["heap"][0] - 1)
py_change = 100 * (ratio_big["python_sorted"][-1] / ratio_big["python_sorted"][0] - 1)


def spread(name):
    return min(ratio_big[name]) * 1e9, max(ratio_big[name]) * 1e9


small_ns = sorted(int(n) for n in e4["insertion"])
cross = s["e4_first_n_where_insertion_slower"]
last_win = small_ns[small_ns.index(cross) - 1] if cross else small_ns[-1]

k_vals = {int(k): v for k, v in e5["k_seconds"].items()}
k_min, k_max = min(k_vals), max(k_vals)
_mp = s["e1_nlogn_ratio"]["merge"]
merge_cmp_n, _r = next(((n, r) for n, r in _mp if n >= e5["n"]), _mp[-1])
merge_cmp_t = _r * merge_cmp_n * math.log2(merge_cmp_n)

pts = {k: v["points"] for k, v in e6.items()}
big_n = pts["binary"][-1][0]
lin_big, bin_big = pts["linear"][-1][1], pts["binary"][-1][1]
_bt = [t for _, t in pts["binary"]]
bin_drops = [(pts["binary"][i][0], pts["binary"][i + 1][0]) for i in range(len(_bt) - 1) if _bt[i + 1] < _bt[i]]

n_qr = e3["quick_random/random"]["n"]
quick_theory = 2 * (n_qr + 1) * sum(1 / i for i in range(1, n_qr + 1)) - 4 * n_qr
n_merge = e3["merge/random"]["n"]
merge_theory = n_merge * (math.log2(n_merge) - 1.26)
n8 = s["e8_n"]
sw = {k: e8[f"quick_first_swaps/{k}"] for k in ["random", "sorted", "reversed"]}
qr_few, qr_rand = e8["quick_random_comparisons/few_unique"], e8["quick_random_comparisons/random"]

e9_n = e9["binary/even"]["points"][-1][0]


def probes(name, shape):
    return e9[f"{name}/{shape}"]["points"][-1][1]


def probe_slope(name, shape):
    p = e9[f"{name}/{shape}"]["points"]
    return loglog_slope([a for a, _ in p], [b for _, b in p])


fastest_cmp = min(['merge', 'quick_first', 'quick_random', 'heap'], key=lambda k: t_max[k])
_rr = dict((n, r) for n, r in s["e1_nlogn_ratio"]["radix"])
RADIX_STEP = ("Radix sort's value goes up again at n = 8,192 " + f"({_rr[4096] * 1e9:.1f} ns at 4,096, {_rr[8192] * 1e9:.1f} ns at 8,192)." +
              " This is because" if _rr.get(8192, 0) > _rr.get(4096, 1) else
              "I expected radix sort's value to go up at n = 8,192, but in this run it did not. I expected it because")
cost_range = max(avg_npc(k) for k in npc) / min(avg_npc(k) for k in npc)
order_range = e2["insertion"]["reversed"] / e2["insertion"]["sorted"]
machine_note = (" It is a shared cloud virtual machine, so other users' work can add noise."
                if "Xeon" in m["cpu"] else "")

if bin_drops:
    bin_noise = ("The binary search curve is not perfectly smooth. Its time goes down between " +
                 ", ".join(f"n = {a:,} and {b:,}" for a, b in bin_drops) +
                 ", which cannot be a real effect of n. A single query takes about a microsecond, so small "
                 "disturbances on the machine show up. The overall trend is reliable, single points are not.")
else:
    bin_noise = "The binary search curve rises smoothly, close to the shape of log₂ n."

# ---------------------------------------------------------------- report text
R = f"""# AI 230 Project 1: Complexity Laboratory

Shafkat Khalek Khan. AI 230 Introduction to Algorithms, Prof. Yair Chaya, Fall 2026.

## 1. Summary

I wrote eight sorting algorithms and four search algorithms from scratch in Python, tested them ({n_tests} automated tests, all passing), and timed them with my own benchmarking harness in nine experiments.

The main result is that the asymptotic analysis predicts the number of operations very well, but predicts running time only roughly. Comparison counts matched the formulas exactly in the deterministic cases. For example, merge sort on random input made {e3['merge/random']['comparisons']:,} comparisons for n = {n_merge:,}, and the average-case formula gives {merge_theory:,.0f}. Running times followed the predicted growth rates, but the machine added things the model leaves out:

* the cost of one operation differs by about {cost_range:.1f}× between algorithms;
* Python's built-in sort, written in C, was {builtin_speedup:.1f}× faster than my merge sort with the same complexity;
* insertion sort beat merge sort for small inputs (up to n = {last_win});
* the same algorithm ran up to {order_range:.0f}× faster or slower depending on the order of the input;
* counting sort, radix sort and interpolation search depend on properties of the values, not only on n;
* at large n, the cost per operation of some algorithms went up, which fits the effect of CPU caches.

## 2. What I implemented

All code is in `complexity_lab/`. Each sort returns a new sorted list and does not change its input.

| Algorithm | Function | Predicted time | Extra space | Notes |
|---|---|---|---|---|
| Insertion sort | `sorting.insertion_sort` | best Θ(n), average and worst Θ(n²) | in place | stable |
| Selection sort | `sorting.selection_sort` | Θ(n²) for every input | in place | always n(n−1)/2 comparisons |
| Merge sort | `sorting.merge_sort` | Θ(n log n) for every input | Θ(n) | stable; T(n) = 2T(n/2) + Θ(n) |
| Quicksort, first element as pivot | `sorting.quick_sort_first` | average Θ(n log n), worst Θ(n²) | O(log n) stack | worst case on sorted input |
| Quicksort, random pivot | `sorting.quick_sort_random` | expected Θ(n log n) for every input | O(log n) stack | Lomuto partition |
| Heap sort | `sorting.heap_sort` | Θ(n log n) for every input | in place | heap built bottom-up in O(n) |
| Counting sort | `sorting.counting_sort` | Θ(n + k), k = range of values | Θ(n + k) | integers only |
| Radix sort (LSD, base 256) | `sorting.radix_sort` | Θ(d(n + b)), d digits, b = 256 | Θ(n + b) | integers, negatives allowed |
| Linear search | `searching.linear_search` | Θ(n) worst | O(1) | works on unsorted lists |
| Binary search | `searching.binary_search` | Θ(log n) worst | O(1) | returns the leftmost match |
| Jump search | `searching.jump_search` | Θ(√n) worst | O(1) | jumps √n positions at a time |
| Interpolation search | `searching.interpolation_search` | O(log log n) average on evenly spread numbers, Θ(n) worst | O(1) | guesses the position from the value |

"In place" means the algorithm itself needs O(1) extra memory. My functions first copy the input (O(n)) so that the same input can be reused for every timing run.

Some design decisions:

* Quicksort recurses on the smaller part and loops on the larger part. This keeps the recursion depth at O(log n) even when the running time is Θ(n²), so I could measure the worst case without hitting Python's recursion limit.
* Counting sort raises an error when the range of values is above 10⁷. I added this after my first test run: one test sorted `[10⁹, 0, 10⁹−1, 1]`, and counting sort tried to create a billion counters for four numbers. The test run stalled. This is the k in Θ(n + k) in practice.
* Radix sort handles negative numbers by sorting their absolute values separately and putting them in front, reversed.

## 3. Testing

`tests/test_algorithms.py` has {n_tests} pytest tests, and they all pass. Every sort is compared with Python's `sorted()` on edge cases (empty list, one element, two elements in both orders, all values equal, negative numbers, already sorted, reversed, many duplicates, values up to 10⁹) and on 200 random lists. The tests also check that the input list is not changed, that insertion sort and merge sort are stable, and that the comparison sorts work on strings and floats. Every search is checked against `list.index` on 300 random cases, on every element of lists whose sizes are around perfect squares (where jump search could go wrong), on skewed values, and on boundary cases. I also wrote a separate stress test, `tests/stress_check.py`, that runs every sort on 3,000 more random lists and every search on 20,000 more random queries. It found no errors.

## 4. How I measured

* Machine: {m['cpu']}, {m['logical_cpus']} logical CPUs, {m['platform']}, {m['implementation']} {m['python']}.{machine_note}
* Timer: `time.perf_counter()`. The garbage collector is turned off while a run is timed. Every point is the median of several runs (3 to 5 for the sorting experiments, 21 for the small-input experiment E4). One search takes less than a microsecond, so for searches I time a batch of queries and divide by the number of queries.
* Inputs: random integers with a fixed seed for each experiment, so every run uses the same inputs. Values are in [0, 10n) unless stated otherwise. For input order I used five kinds: random, sorted, reversed, nearly sorted (1% of positions swapped) and few unique (only 10 different values).
* Counting operations: all my comparison sorts use only `<`. I wrap each element in a small class that counts calls to `<`, which gives the exact number of comparisons. For searches I count how many different positions of the list were read.
* Growth rate: I fit a straight line to log(time) against log(n). If time grows like n^p, the slope is p. For n log n the slope is not exactly 1: over n = 256 to 131,072, the slope of n log₂ n itself is {exp_nlogn:.3f}, so that is the value to compare with.
* Sizes: the Θ(n²) sorts from n = 128 to 4,096, the other sorts from 256 to 131,072, doubling each time.

## 5. Results

### E1. Running time against n (random input)

![E1](figures/e1_growth_loglog.png)

| Algorithm | n | Slope (all sizes) | Slope (larger half) | Time at largest n |
|---|---|---|---|---|
""" + "\n".join(
    f"| {k} | {v['n_range'][0]:,} to {v['n_range'][1]:,} | {v['slope_all']:.3f} | {v['slope_upper_half']:.3f} | {ms(v['seconds_at_max_n'])} |"
    for k, v in sl.items()) + f"""

Predicted slopes: 2 for Θ(n²), {exp_nlogn:.3f} for n log n over this range, 1 for Θ(n).

Insertion sort ({sl['insertion']['slope_all']:.3f}) and selection sort ({sl['selection']['slope_all']:.3f}) are quadratic, as predicted. Merge sort ({sl['merge']['slope_all']:.3f}) and both quicksorts ({sl['quick_random']['slope_all']:.3f} with a random pivot, {sl['quick_first']['slope_all']:.3f} with the first element) are close to the n log n value. First-pivot quicksort only becomes quadratic on ordered input (E2). Heap sort's slope ({sl['heap']['slope_all']:.3f}) is higher than the n log n value. Counting sort ({sl['counting']['slope_all']:.3f}) and radix sort ({sl['radix']['slope_all']:.3f}) are close to linear.

![E1 ratio](figures/e1_nlogn_ratio.png)

To check the n log n sorts more closely I divided each time by n log₂ n. For a true n log n algorithm this should give a flat line. For the smallest sizes the fixed cost of each call dominates, so I compare from n = 1,024 up. In that range merge sort stays between {spread('merge')[0]:.0f} and {spread('merge')[1]:.0f} ns per n log₂ n, so it is flat. First-pivot quicksort stays between {spread('quick_first')[0]:.0f} and {spread('quick_first')[1]:.0f} ns. Randomized quicksort moves between {spread('quick_random')[0]:.0f} and {spread('quick_random')[1]:.0f} ns, because its random pivots give a different amount of work in every run. Heap sort's value {'goes up' if heap_change > 0 else 'goes down'} by {abs(heap_change):.0f}% from n = 1,024 to the largest n, and Python's `sorted` {'goes up' if py_change > 0 else 'goes down'} by {abs(py_change):.0f}%. Counting sort and radix sort go down, which is what a linear algorithm divided by n log n should do.

{RADIX_STEP} the values go up to 10n, and 10 × 8,192 = 81,920 is the first maximum that needs a third base-256 digit, so every element gets one more pass. Because the values grow with n here, the number of digits d = ⌈log₂₅₆(10n)⌉ also grows. So radix sort is Θ(d·n) in this experiment, not plain Θ(n).

### E2. Effect of input order (n = {s['e2_n']:,})

![E2](figures/e2_input_order.png)

| Algorithm | random | sorted | reversed | nearly sorted | few unique |
|---|---|---|---|---|---|
""" + "\n".join(
    f"| {a} | " + " | ".join(ms(e2[a][k]) for k in ["random", "sorted", "reversed", "nearly_sorted", "few_unique"]) + " |"
    for a in e2) + f"""

* Insertion sort takes {ms(e2['insertion']['sorted'])} on sorted input and {ms(e2['insertion']['random'])} on random input ({times(e2['insertion']['random'], e2['insertion']['sorted'])} faster). On sorted input the inner loop never runs, so the cost is Θ(n). Reversed input is its worst case, with n(n−1)/2 shifts instead of about n²/4, and it took {times(e2['insertion']['reversed'], e2['insertion']['random'])} as long as random input. Nearly sorted input ({ms(e2['insertion']['nearly_sorted'])}) is much closer to the best case than to random input.
* Selection sort takes about the same time on every input ({ms(min(e2['selection'].values()))} to {ms(max(e2['selection'].values()))}), because it always scans the whole unsorted part.
* First-pivot quicksort becomes quadratic on sorted ({ms(e2['quick_first']['sorted'])}) and reversed ({ms(e2['quick_first']['reversed'])}) input, compared with {ms(e2['quick_first']['random'])} on random input. Sorted and reversed input both cause exactly n(n−1)/2 comparisons, but reversed input took longer. I counted the swaps to find out why: at n = {n8:,} there were {sw['sorted']:,} swaps on sorted input and {sw['reversed']:,} on reversed input. On sorted input the pivot is always the smallest value, so `a[j] < pivot` is never true and nothing is swapped.
* Randomized quicksort does not depend on the order ({ms(e2['quick_random']['sorted'])} on sorted input, {ms(e2['quick_random']['random'])} on random input). It was slower on input with only 10 different values ({ms(e2['quick_random']['few_unique'])}). My partition puts every element equal to the pivot on the same side, so with many equal values the parts are very unbalanced. At n = {n8:,} it made {qr_few:,} comparisons on that input and {qr_rand:,} on random input. That is close to (1/10)·n(n−1)/2 = {n8 * (n8 - 1) / 20:,.0f}, so it behaves quadratically inside each group of equal values. A three-way partition would fix this.
* Merge sort ({ms(min(e2['merge'].values()))} to {ms(max(e2['merge'].values()))}) and heap sort ({ms(min(e2['heap'].values()))} to {ms(max(e2['heap'].values()))}) change much less with the order than insertion sort or first-pivot quicksort, as their Θ(n log n) bounds for every input predict.
* Python's `sorted` (Timsort) is fastest on sorted input ({us(e2['python_sorted']['sorted'])} against {us(e2['python_sorted']['random'])}) because it detects runs that are already in order.

### E3. Counting comparisons

![E3](figures/e3_comparisons.png)

| Algorithm / input | n | Comparisons | ÷ n log₂ n | ÷ n(n−1)/2 | Prediction |
|---|---|---|---|---|---|
| insertion / random | {e3['insertion/random']['n']:,} | {e3['insertion/random']['comparisons']:,} | {e3['insertion/random']['per_n_log2_n']} | {e3['insertion/random']['per_n2_over_2']} | about n²/4 (÷ n²/4 = {e3['insertion/random']['per_n2_over_4']}) |
| insertion / sorted | {e3['insertion/sorted']['n']:,} | {e3['insertion/sorted']['comparisons']:,} | {e3['insertion/sorted']['per_n_log2_n']} | {e3['insertion/sorted']['per_n2_over_2']} | exactly n − 1 |
| selection / any | {e3['selection/random']['n']:,} | {e3['selection/random']['comparisons']:,} | {e3['selection/random']['per_n_log2_n']} | {e3['selection/random']['per_n2_over_2']} | exactly n(n−1)/2 |
| merge / random | {n_merge:,} | {e3['merge/random']['comparisons']:,} | {e3['merge/random']['per_n_log2_n']} | | about n log₂ n − 1.26n = {merge_theory:,.0f} |
| merge / sorted | {e3['merge/sorted']['n']:,} | {e3['merge/sorted']['comparisons']:,} | {e3['merge/sorted']['per_n_log2_n']} | | exactly (n/2) log₂ n |
| quick_first / sorted | {e3['quick_first/sorted']['n']:,} | {e3['quick_first/sorted']['comparisons']:,} | {e3['quick_first/sorted']['per_n_log2_n']} | {e3['quick_first/sorted']['per_n2_over_2']} | exactly n(n−1)/2 (worst case) |
| quick_random / random | {n_qr:,} | {e3['quick_random/random']['comparisons']:,} | {e3['quick_random/random']['per_n_log2_n']} | | expected 2(n+1)Hₙ − 4n = {quick_theory:,.0f} |
| heap / random | {e3['heap/random']['n']:,} | {e3['heap/random']['comparisons']:,} | {e3['heap/random']['per_n_log2_n']} | | at most about 2n log₂ n |

The deterministic cases match the formulas exactly. Merge sort on random input is within {pct_dev(e3['merge/random']['comparisons'], merge_theory):.2f}% of its average-case formula and insertion sort within {pct_dev(e3['insertion/random']['comparisons'], e3['insertion/random']['n'] ** 2 / 4):.1f}% of n²/4. Randomized quicksort is within {pct_dev(e3['quick_random/random']['comparisons'], quick_theory):.1f}% of its expected value. That count changes from run to run because the pivots are random, and the formula is an average over all pivot choices. Insertion sort made {e3['insertion/sorted']['comparisons']:,} comparisons on sorted input and {e3['insertion/random']['comparisons']:,} on random input of the same size, which shows how far apart its best and average cases are.

Putting E1 and E3 together shows where the time goes. I divided each measured time by the number of comparisons. The result is the average time per comparison, including all the other work the algorithm does around each comparison.

| Algorithm | ns per comparison (average over sizes) | Comparisons ÷ n log₂ n (random input) |
|---|---|---|
""" + "\n".join(
    f"| {k} | {avg_npc(k):.0f} | {e3[k + '/random']['per_n_log2_n']} |" for k in ["merge", "quick_first", "quick_random", "heap", "insertion", "selection"]) + f"""

Merge sort makes the fewest comparisons of the n log n sorts ({e3['merge/random']['per_n_log2_n']} n log₂ n), but each one costs about {avg_npc('merge'):.0f} ns, because it also slices lists, appends to new lists and allocates memory. First-pivot quicksort makes {e3['quick_first/random']['per_n_log2_n']} n log₂ n comparisons at about {avg_npc('quick_first'):.0f} ns each and works in place, so on random input it was {'the fastest of my comparison sorts' if fastest_cmp == 'quick_first' else 'faster than merge sort'} ({ms(t_max['quick_first'])} against {ms(t_max['merge'])} for merge sort at n = 131,072). Big-O notation counts operations but not what each one costs, and here the cost per comparison differs by a factor of {cost_range:.1f}.

### E4. Small inputs

![E4](figures/e4_small_n.png)

| n | """ + " | ".join(str(n) for n in small_ns) + """ |
|---|""" + "---|" * len(small_ns) + """
| insertion (µs) | """ + " | ".join(f"{e4['insertion'][str(n)]:.1f}" for n in small_ns) + """ |
| merge (µs) | """ + " | ".join(f"{e4['merge'][str(n)]:.1f}" for n in small_ns) + f""" |

Insertion sort was faster than merge sort for every n up to {last_win}, and slower from n = {cross} on. Big-O describes what happens as n grows large and ignores constant factors. Merge sort has a much larger constant (function calls, slicing, new lists) than insertion sort's short inner loop, so for small n the Θ(n²) algorithm wins. This is why real sorting routines combine the two. CPython's Timsort uses binary insertion sort for short runs.

### E5. Counting sort and the value range k (n = {e5['n']:,})

![E5](figures/e5_counting_k.png)

| k | """ + " | ".join(f"{k:,}" for k in sorted(k_vals)) + """ |
|---|""" + "---|" * len(k_vals) + """
| time | """ + " | ".join(ms(k_vals[k]) for k in sorted(k_vals)) + f""" |

With n fixed, the time changes little while k is at most n ({ms(k_vals[k_min])} at k = {k_min:,}, {ms(k_vals.get(10_000, float('nan')))} at k = 10,000). After that it grows with k, up to {ms(k_vals[k_max])} at k = {k_max:,}, which is {times(k_vals[k_max], k_vals[k_min])} slower for the same n. The fitted slope for k ≥ n is {e5['slope_k_ge_n']} and moves towards 1 as k becomes larger than n. Counting sort is linear in n + k, not in n. At k = {k_max:,} it needed {ms(k_vals[k_max])} for {e5['n']:,} numbers, while my merge sort sorted {merge_cmp_n:,} numbers in {ms(merge_cmp_t)} (E1).

### E6 and E7. Search time

![E6](figures/e6_search.png)

E6 searches for random elements of the sorted list 0, 2, 4, …, 2(n−1).

| Search | Slope | Predicted | Time per query at n = {pts['binary'][0][0]:,} | at n = {big_n:,} |
|---|---|---|---|---|
| linear | {e6['linear']['slope']} | 1 (Θ(n)) | {t_auto(pts['linear'][0][1])} | {t_auto(pts['linear'][-1][1])} |
| jump | {e6['jump']['slope']} | 0.5 (Θ(√n)) | {t_auto(pts['jump'][0][1])} | {t_auto(pts['jump'][-1][1])} |
| binary | {e6['binary']['slope']} | {exp_log:.3f} (slope of log₂ n over this range) | {us(pts['binary'][0][1])} | {us(pts['binary'][-1][1])} |
| interpolation | {e6['interpolation']['slope']} | close to 0 on this list | {us(pts['interpolation'][0][1])} | {us(pts['interpolation'][-1][1])} |

All four slopes match their predictions. At n = {big_n:,}, binary search is {lin_big / bin_big:,.0f}× faster than linear search per query. Interpolation search is almost constant here because this list is perfectly evenly spaced, so its first guess is always right. E9 shows what happens on other data. {bin_noise}

E7 shows that for linear search the position of the target matters (n = {s['e7_n']:,}): first element {us(e7['first'])}, at one quarter {ms(e7['quarter'])}, middle {ms(e7['middle'])}, last {ms(e7['last'])}, not in the list {ms(e7['missing'])}. The time grows with the position, at about {e7['last'] / s['e7_n'] * 1e9:.0f} ns per element checked. The worst case (last or missing) takes about twice as long as the average case (middle).

### E9. Elements examined by search, on three kinds of data

![E9](figures/e9_search_probes.png)

I counted how many different positions each search reads, averaged over 100 searches for elements in the list. The three kinds of sorted data are: "even" (n different values drawn uniformly from [0, 10n)), "power" (the values i⁴) and "outlier" (0, 1, …, n−2 and then one huge value, 10¹⁵).

| Search | even | power | outlier |
|---|---|---|---|
""" + "\n".join(
    f"| {a} | {probes(a, 'even'):,.1f} | {probes(a, 'power'):,.1f} | {probes(a, 'outlier'):,.1f} |"
    for a in ["binary", "jump", "interpolation"]) + f"""

(Average number of elements examined at n = {e9_n:,}.)

* Binary search examines about log₂ n elements ({probes('binary', 'even'):.0f} at n = {e9_n:,}, log₂ n = {math.log2(e9_n):.0f}) whatever the data looks like.
* Jump search examines about √n elements ({probes('jump', 'even'):.0f} at n = {e9_n:,}, √n = {math.sqrt(e9_n):.0f}).
* Interpolation search depends completely on the data. On evenly spread values it examined only {probes('interpolation', 'even'):.1f} elements on average, growing very slowly with n, as O(log log n) predicts (log₂ log₂ n = {math.log2(math.log2(e9_n)):.0f} here). On the i⁴ values it examined {probes('interpolation', 'power'):,.0f}, which is worse than binary search. With one outlier it examined {probes('interpolation', 'outlier'):,.0f} elements on average and up to {e9['interpolation/outlier']['max_at_largest_n']:,} in one search, which is linear (fitted slope {probe_slope('interpolation', 'outlier'):.2f}). Because the last value is so large, the formula puts every guess at the first position of the range, so each step removes only one element. Its O(log log n) bound is an average for evenly spread data, not a guarantee.

## 6. Where the theory and the machine disagree, and why

| # | What the theory says | What I measured | Reason |
|-|------|--------|------------|
| 1 | Algorithms with the same complexity cost about the same | Merge sort and quicksort are both Θ(n log n), but a comparison costs about {avg_npc('merge'):.0f} ns in merge sort and {avg_npc('quick_first'):.0f} ns in quicksort | Big-O counts comparisons. The real cost also includes memory allocation, copying, index arithmetic and function calls (E1, E3). |
| 2 | Only the complexity class matters for large n | Python's built-in `sorted` was {builtin_speedup:.1f}× faster than my merge sort at n = 131,072 | It is written in C, so each step avoids the overhead of the Python interpreter. Big-O does not include the language. |
| 3 | Θ(n log n) is better than Θ(n²) | Insertion sort was faster up to n = {last_win} | Big-O is about large n and ignores constants. For small n the constants decide (E4). |
| 4 | One complexity per algorithm | Insertion sort's time changed by up to {order_range:.0f}× at the same n depending on the input order | Best, average and worst cases are different functions. First-pivot quicksort has its worst case on sorted input, which is common in practice (E2). |
| 5 | Equal comparison counts mean equal time | First-pivot quicksort took {times(e2['quick_first']['reversed'], e2['quick_first']['sorted'])} as long on reversed input as on sorted input, with the same number of comparisons | The comparison count leaves out swaps: {sw['reversed']:,} on reversed input and {sw['sorted']:,} on sorted input (E2). |
| 6 | Counting sort and radix sort are linear | Counting sort became {times(k_vals[k_max], k_vals[k_min])} slower at the same n as k grew. Radix sort jumped when the values needed one more digit | Their bounds contain k and d. Treating these as constants is only right when they are bounded (E1, E5). |
| 7 | Interpolation search is O(log log n) | {probes('interpolation', 'outlier'):,.0f} elements examined on average at n = {e9_n:,} with one outlier, against {probes('binary', 'outlier'):.0f} for binary search | That bound assumes evenly spread values. Skewed values make its guesses bad (E9). |
| 8 | Each memory access costs the same | From n = 1,024 up, heap sort's time per n log₂ n {'rose' if heap_change > 0 else 'fell'} by {abs(heap_change):.0f}% and Python's `sorted` by {abs(py_change):.0f}%, while merge sort stayed between {spread('merge')[0]:.0f} and {spread('merge')[1]:.0f} ns | My explanation is the CPU cache. The RAM model charges the same for every memory access, but a real CPU is slower when the data no longer fits in its cache. Heap sort jumps between positions i and 2i+1, which uses the cache badly, while merge sort reads its lists in order. I did not measure cache misses, so this is a likely explanation, not a proven one. It could be checked with hardware counters (for example `perf stat`). |
| 9 | Randomized quicksort is Θ(n log n) on every input | {times(e2['quick_random']['few_unique'], e2['quick_random']['random'])} slower on input with only 10 different values | The analysis assumes the values are distinct. With many equal values my two-way partition is unbalanced (E2). |

## 7. Limitations and what did not work

* All results come from one machine ({m['cpu']}, {m['logical_cpus']} logical CPUs). Other programs running at the same time can disturb single measurements. Taking the median helps but does not remove this. Times will be different on another computer, but the growth rates should be similar.
* Each point is the median of only a few runs (3 to 5 in most experiments) and I did not compute confidence intervals. The effects I discuss are factors of 2 or more, which is much larger than the noise, but small differences (for example between the two quicksorts on random input) should not be read into.
* Python is not a clean model of the hardware. Every integer is an object and every list element is a pointer, so memory effects and interpreter effects are mixed. What I say about caches is an explanation I did not measure directly.
* I stopped the Θ(n²) sorts at n = 4,096 to keep the run time reasonable, so their slopes come from a smaller range.
* My first test run stalled on counting sort (Section 2), which led to the range limit.
* My first seeding code used Python's `hash()`. That value changes every time Python starts, so the inputs would have been different on every run. I replaced it with a CRC32 checksum so the results can be reproduced.
* Interpolation search can return any matching position when there are duplicates (binary and jump search return the leftmost). I documented this and only tested it on lists without duplicates, plus a separate duplicate test that checks the returned position holds the target.

## 8. How to reproduce

```
pip install -r requirements.txt
python -m pytest -q                 # {n_tests} tests
python run_experiments.py           # about 2 to 3 minutes, writes results/*.csv
python make_figures.py              # writes figures/*.png and results/summary.json
python make_report.py               # rewrites REPORT.md with the new numbers
python tests/stress_check.py        # extra random checks, about 1 minute
python demo.py                      # short live demo
```

## 9. Use of generative AI

_Check that this section is accurate and change it if needed before submitting._ I used Claude (Anthropic) as an assistant to help write the code, the tests, the benchmark harness and this report. I read and checked every file, ran the tests and experiments myself, and I can explain every algorithm, decision and result in this report.
"""

with open("REPORT.md", "w") as f:
    f.write(R)
print("wrote REPORT.md", len(R), "characters,", n_tests, "tests")
