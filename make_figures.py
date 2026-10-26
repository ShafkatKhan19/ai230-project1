"""Read results/*.csv, write figures/*.png and results/summary.json (fitted slopes etc.)."""

import csv
import json
import math
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from complexity_lab.harness import loglog_slope

RESULTS, FIGURES = "results", "figures"
plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3})


def read(name):
    with open(os.path.join(RESULTS, f"{name}.csv")) as f:
        return list(csv.DictReader(f))


def save(fig, name):
    path = os.path.join(FIGURES, f"{name}.png")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    print("  wrote", path)


def by(rows, *keys):
    out = defaultdict(list)
    for r in rows:
        out[tuple(r[k] for k in keys) if len(keys) > 1 else r[keys[0]]].append(r)
    return out


summary = {}

# ---- E1: growth -----------------------------------------------------------
e1 = by(read("e1_growth"), "algorithm")
fig, ax = plt.subplots(figsize=(7, 4.4))
slopes, nlogn_ratio = {}, {}
for name, rows in e1.items():
    ns = [int(r["n"]) for r in rows]
    ts = [float(r["seconds"]) for r in rows]
    ax.loglog(ns, ts, "o-", ms=3, label=name)
    half = len(ns) // 2                                  # fit on the larger half of the sizes
    slopes[name] = {"slope_all": round(loglog_slope(ns, ts), 3),
                    "slope_upper_half": round(loglog_slope(ns[half:], ts[half:]), 3),
                    "n_range": [ns[0], ns[-1]],
                    "seconds_at_max_n": ts[-1]}
    nlogn_ratio[name] = [(n, t / (n * math.log2(n))) for n, t in zip(ns, ts)]
ax.set_xlabel("n (random integers)")
ax.set_ylabel("median time (s)")
ax.set_title("E1  Running time vs input size (log-log)")
ax.legend(fontsize=7, ncol=2)
save(fig, "e1_growth_loglog")
summary["e1_slopes"] = slopes

fig, ax = plt.subplots(figsize=(7, 3.8))
for name in ["merge", "heap", "quick_random", "quick_first", "radix", "counting", "python_sorted"]:
    pts = nlogn_ratio[name]
    base = pts[0][1]
    ax.semilogx([p[0] for p in pts], [p[1] / base for p in pts], "o-", ms=3, label=name)
ax.axhline(1, color="k", lw=0.8)
ax.set_xlabel("n")
ax.set_ylabel("T(n) / (n log2 n), relative to smallest n")
ax.set_title("E1  Is T(n) proportional to n log n?  (flat line = yes)")
ax.legend(fontsize=7, ncol=2)
save(fig, "e1_nlogn_ratio")
summary["e1_nlogn_ratio"] = {k: [[n, r] for n, r in v] for k, v in nlogn_ratio.items()}

# ---- E2: input order -------------------------------------------------------
e2 = read("e2_input_order")
algos = list(dict.fromkeys(r["algorithm"] for r in e2))
inputs = list(dict.fromkeys(r["input"] for r in e2))
table = {(r["algorithm"], r["input"]): float(r["seconds"]) for r in e2}
fig, ax = plt.subplots(figsize=(8, 4))
w = 0.8 / len(inputs)
for i, kind in enumerate(inputs):
    ax.bar([j + i * w for j in range(len(algos))], [table[(a, kind)] for a in algos], w, label=kind)
ax.set_yscale("log")
ax.set_xticks([j + 0.4 - w / 2 for j in range(len(algos))], algos, rotation=20)
ax.set_ylabel("median time (s), log scale")
ax.set_title(f"E2  Effect of input order (n = {e2[0]['n']})")
ax.legend(fontsize=7, ncol=5)
save(fig, "e2_input_order")
summary["e2_seconds"] = {a: {k: table[(a, k)] for k in inputs} for a in algos}
summary["e2_n"] = int(e2[0]["n"])

# ---- E3: comparisons -------------------------------------------------------
e3 = read("e3_comparisons")
fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
ratios = {}
for ax, kind in zip(axes, ["random", "sorted"]):
    for (name, k), rows in by(e3, "algorithm", "input").items():
        if k != kind:
            continue
        ns = [int(r["n"]) for r in rows]
        cs = [int(r["comparisons"]) for r in rows]
        ax.loglog(ns, cs, "o-", ms=3, label=name)
        ratios[f"{name}/{kind}"] = {
            "n": ns[-1], "comparisons": cs[-1],
            "per_n_log2_n": round(cs[-1] / (ns[-1] * math.log2(ns[-1])), 3),
            "per_n2_over_2": round(cs[-1] / (ns[-1] * (ns[-1] - 1) / 2), 4),
            "per_n2_over_4": round(cs[-1] / (ns[-1] ** 2 / 4), 3),
            "slope": round(loglog_slope(ns, cs), 3)}
    ns_ref = sorted({int(r["n"]) for r in e3})
    ax.loglog(ns_ref, [n * math.log2(n) for n in ns_ref], "k--", lw=1, label="n log2 n")
    ax.loglog(ns_ref, [n * n / 2 for n in ns_ref], "k:", lw=1, label="n^2 / 2")
    ax.set_title(f"E3  Comparisons, {kind} input")
    ax.set_xlabel("n")
axes[0].set_ylabel("number of < comparisons")
axes[1].legend(fontsize=6)
save(fig, "e3_comparisons")
summary["e3_ratios"] = ratios

# time per comparison: links machine time (E1) to the machine-independent count (E3)
per_cmp = {}
e1_lookup = {(r["algorithm"], int(r["n"])): float(r["seconds"]) for r in read("e1_growth")}
for r in e3:
    if r["input"] == "random" and (r["algorithm"], int(r["n"])) in e1_lookup:
        per_cmp.setdefault(r["algorithm"], []).append(
            [int(r["n"]), 1e9 * e1_lookup[(r["algorithm"], int(r["n"]))] / int(r["comparisons"])])
summary["ns_per_comparison"] = per_cmp

# ---- E4: small n -----------------------------------------------------------
e4 = by(read("e4_small_n"), "algorithm")
fig, ax = plt.subplots(figsize=(6, 3.6))
small = {}
for name, rows in e4.items():
    ns = [int(r["n"]) for r in rows]
    ts = [float(r["seconds"]) * 1e6 for r in rows]
    ax.plot(ns, ts, "o-", ms=3, label=name)
    small[name] = dict(zip(ns, ts))
cross = next((n for n in sorted(small["insertion"]) if small["insertion"][n] > small["merge"][n]), None)
ax.set_xlabel("n")
ax.set_ylabel("time per sort (microseconds)")
ax.set_title("E4  Small inputs: insertion vs merge")
if cross:
    ax.axvline(cross, color="grey", ls="--", lw=1)
ax.legend()
save(fig, "e4_small_n")
summary["e4_microseconds"] = small
summary["e4_first_n_where_insertion_slower"] = cross

# ---- E5: counting sort vs k ------------------------------------------------
e5 = read("e5_counting_k")
ks = [int(r["k"]) for r in e5]
ts = [float(r["seconds"]) for r in e5]
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.loglog(ks, ts, "o-")
ax.axvline(int(e5[0]["n"]), color="grey", ls="--", lw=1, label=f"k = n = {int(e5[0]['n']):,}")
ax.set_xlabel("value range k")
ax.set_ylabel("median time (s)")
ax.set_title(f"E5  Counting sort, fixed n = {int(e5[0]['n']):,}")
ax.legend()
save(fig, "e5_counting_k")
summary["e5"] = {"n": int(e5[0]["n"]), "k_seconds": dict(zip(ks, ts)),
                 "slope_k_ge_n": round(loglog_slope([k for k in ks if k >= int(e5[0]["n"])],
                                                    [t for k, t in zip(ks, ts) if k >= int(e5[0]["n"])]), 3)}

# ---- E6: search ------------------------------------------------------------
e6 = by(read("e6_search"), "algorithm")
fig, ax = plt.subplots(figsize=(6, 3.6))
search = {}
for name, rows in e6.items():
    ns = [int(r["n"]) for r in rows]
    ts = [float(r["seconds_per_query"]) for r in rows]
    ax.loglog(ns, ts, "o-", ms=3, label=name)
    search[name] = {"points": [[n, t] for n, t in zip(ns, ts)], "slope": round(loglog_slope(ns, ts), 3)}
ax.set_xlabel("n (sorted list)")
ax.set_ylabel("time per query (s)")
ax.set_title("E6  Search time per query (evenly spaced sorted list)")
ax.legend()
save(fig, "e6_search")
summary["e6"] = search

# ---- E7 --------------------------------------------------------------------
e7 = read("e7_linear_position")
summary["e7"] = {r["position"]: float(r["seconds"]) for r in e7}
summary["e7_n"] = int(e7[0]["n"])

# ---- E9: search probes on different data shapes ---------------------------
e9 = read("e9_search_probes")
shapes = list(dict.fromkeys(r["shape"] for r in e9))
fig, axes = plt.subplots(1, len(shapes), figsize=(10, 3.4), sharey=True)
probes = {}
for ax, shape in zip(axes, shapes):
    for name, rows in by([r for r in e9 if r["shape"] == shape], "algorithm").items():
        ns = [int(r["n"]) for r in rows]
        mp = [float(r["mean_probes"]) for r in rows]
        ax.loglog(ns, mp, "o-", ms=3, label=name)
        probes[f"{name}/{shape}"] = {"points": [[n, v] for n, v in zip(ns, mp)],
                                     "max_at_largest_n": int(rows[-1]["max_probes"])}
    ax.set_title(f"E9  {shape} values")
    ax.set_xlabel("n")
axes[0].set_ylabel("distinct elements examined per search")
axes[-1].legend(fontsize=7)
save(fig, "e9_search_probes")
summary["e9"] = probes

summary["e8"] = {f"{r['measure']}/{r['input']}": int(r["value"]) for r in read("e8_quicksort_details")}
summary["e8_n"] = int(read("e8_quicksort_details")[0]["n"])

with open(os.path.join(RESULTS, "machine.json")) as f:
    summary["machine"] = json.load(f)
with open(os.path.join(RESULTS, "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
print("  wrote results/summary.json")
