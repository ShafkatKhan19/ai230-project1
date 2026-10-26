# AI 230 Project 1: Complexity Laboratory

Sorting and searching algorithms implemented from scratch, a benchmarking harness, and a report that compares measured running times with asymptotic predictions. The full write-up is in **[REPORT.md](REPORT.md)**.

## Layout

```
complexity_lab/
  sorting.py      insertion, selection, merge, quicksort (first / random pivot), heap, counting, radix
  searching.py    linear, binary, jump and interpolation search
  harness.py      input generators, timer (median, GC off), comparison and probe counters, log-log slope fit
tests/
  test_algorithms.py   126 correctness tests (pytest)
  stress_check.py      extra random checks (3,000 lists, 20,000 queries)
run_experiments.py     experiments E1-E9 -> results/*.csv
demo.py                short live demo for the defense
make_figures.py        results/*.csv -> figures/*.png + results/summary.json
make_report.py         results/summary.json -> REPORT.md
results/  figures/     output of the committed run
```

## Run it

Python 3.11 or later.

```
pip install -r requirements.txt
python -m pytest -q
python tests/stress_check.py
python run_experiments.py          # add --quick for a 15-second smoke test
python make_figures.py
python make_report.py
```

`run_experiments.py` takes about 2–3 minutes. Re-running it overwrites `results/` and `figures/` with the numbers of the machine you run it on; `make_report.py` then rebuilds `REPORT.md` from them (read it once afterwards to check that the prose still fits the new numbers).

## Live demo

`python demo.py` prints comparison counts, a worst-case quicksort timing, linear vs binary search, and interpolation search on even vs skewed data. Or in a Python shell:

```python
from complexity_lab.sorting import quick_sort_first, merge_sort
from complexity_lab.harness import count_comparisons
data = list(range(2000))
count_comparisons(quick_sort_first, data)   # 1,999,000 = n(n-1)/2: the worst case on sorted input
count_comparisons(merge_sort, data)          # 10,864: about (n/2) log2 n
```
