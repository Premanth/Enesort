#!/usr/bin/env python3
"""
show_table1.py  –  Generate and execute Table 1 for Enesort
Table 1: Execution Time and Speedup Comparison across 8 Workloads (N = 100,000, 32-bit Integers)

Usage:
  python scripts/show_table1.py          # Instant output from logged 24,210-trial dataset
  python scripts/show_table1.py --run    # Execute fresh benchmark trials live via bench.exe
  python scripts/show_table1.py --latex  # Output LaTeX table code for paper submission
"""

import os
import sys
import argparse
import subprocess
import platform
import numpy as np
import pandas as pd

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMMARY_CSV = os.path.join(PROJ_DIR, "results", "analysis", "summary.csv")
BENCH_EXE = os.path.join(PROJ_DIR, "build_manual", "bench.exe" if platform.system() == "Windows" else "bench")

WORKLOADS = [
    "all_equal",
    "ascending",
    "descending",
    "few_distinct_10",
    "median_of_3_killer",
    "organ_pipe",
    "uniform_random",
    "sorted_append_100"
]

ALGORITHMS = [
    "enesort",
    "std_sort",
    "pdqsort",
    "timsort",
    "mergesort",
    "heapsort",
    "mo3_quicksort",
    "yaroslavskiy"
]

ALGO_HEADERS = {
    "enesort": "Enesort (Ours)",
    "std_sort": "std::sort",
    "pdqsort": "pdqsort",
    "timsort": "TimSort",
    "mergesort": "MergeSort",
    "heapsort": "HeapSort",
    "mo3_quicksort": "MO3-QSort",
    "yaroslavskiy": "Yaroslavskiy"
}

def load_from_summary():
    if not os.path.exists(SUMMARY_CSV):
        print(f"Error: {SUMMARY_CSV} not found. Run analysis first or use --run.", file=sys.stderr)
        sys.exit(1)
    df = pd.read_csv(SUMMARY_CSV)
    sub = df[(df["n"] == 100000) & (df["type"] == "int32") & 
             (df["algorithm"].isin(ALGORITHMS)) & (df["workload"].isin(WORKLOADS))]
    pivot = sub.pivot(index="workload", columns="algorithm", values="median_ns") / 1e6  # ms
    return pivot.reindex(WORKLOADS)[ALGORITHMS]

def run_live_benchmark(trials=5):
    if not os.path.exists(BENCH_EXE):
        print(f"Error: Benchmark executable not found at {BENCH_EXE}", file=sys.stderr)
        sys.exit(1)

    print(f"\n[+] Executing live benchmark for Table 1 (N=100,000, type=int32, trials={trials})...")
    records = []
    
    for algo in ALGORITHMS:
        for wload in WORKLOADS:
            cmd = [
                BENCH_EXE,
                "--study", "main",
                "--algo", algo,
                "--type", "int32",
                "--sizes", "100000",
                "--trials", str(trials),
                "--workload", wload
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"Error running {algo} on {wload}: {res.stderr}", file=sys.stderr)
                continue
            
            times = []
            for line in res.stdout.strip().splitlines():
                if line.startswith("timestamp") or not line.strip():
                    continue
                parts = line.split(",")
                if len(parts) >= 12:
                    try:
                        times.append(float(parts[11]))
                    except ValueError:
                        pass
            if times:
                med_ms = np.median(times) / 1e6
                records.append({"algorithm": algo, "workload": wload, "median_ms": med_ms})
                print(f"    - {algo:<15} on {wload:<20}: {med_ms:8.3f} ms")

    live_df = pd.DataFrame(records)
    pivot = live_df.pivot(index="workload", columns="algorithm", values="median_ms")
    return pivot.reindex(WORKLOADS)[ALGORITHMS]

def print_table_markdown(pivot):
    pivot = pivot.copy()
    pivot["Speedup vs std::sort"] = pivot["std_sort"] / pivot["enesort"]
    
    headers = ["Workload (N=100k)"] + [ALGO_HEADERS[a] for a in ALGORITHMS] + ["Speedup vs std::sort"]
    print("\n" + "=" * 115)
    print("TABLE I: EXECUTION TIME AND SPEEDUP COMPARISON ACROSS 8 WORKLOADS (N = 100,000, 32-BIT INTEGERS)")
    print("=" * 115)
    
    header_line = "| " + " | ".join(headers) + " |"
    sep_line    = "| " + " | ".join(["---"] * len(headers)) + " |"
    print(header_line)
    print(sep_line)
    
    for wload in WORKLOADS:
        row_vals = [f"**{wload}**"]
        for a in ALGORITHMS:
            val = pivot.loc[wload, a]
            row_vals.append(f"{val:.3f} ms")
        speedup = pivot.loc[wload, "Speedup vs std::sort"]
        row_vals.append(f"**{speedup:.2f}x**")
        print("| " + " | ".join(row_vals) + " |")
    print("=" * 115 + "\n")

def print_table_latex(pivot):
    pivot = pivot.copy()
    pivot["speedup"] = pivot["std_sort"] / pivot["enesort"]
    
    cols = ["l"] + ["r"] * len(ALGORITHMS) + ["r"]
    print("\n% LaTeX Code for Table 1:")
    print(r"\begin{table*}[t]")
    print(r"\centering")
    print(r"\caption{Execution Time (ms) and Speedup Ratio across 8 Representative Workloads ($N=100,000$, 32-bit Integers)}")
    print(r"\label{tab:table1_results}")
    print(r"\begin{tabular}{" + "".join(cols) + "}")
    print(r"\toprule")
    header_str = "Workload & " + " & ".join([ALGO_HEADERS[a] for a in ALGORITHMS]) + r" & Speedup vs \texttt{std::sort} \\"
    print(header_str)
    print(r"\midrule")
    for w in WORKLOADS:
        row_items = [w.replace("_", r"\_")]
        for a in ALGORITHMS:
            v = pivot.loc[w, a]
            row_items.append(f"{v:.3f}")
        s = pivot.loc[w, "speedup"]
        row_items.append(rf"\textbf{{{s:.2f}$\times$}}")
        print(" & ".join(row_items) + r" \\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\end{table*}" + "\n")

def main():
    parser = argparse.ArgumentParser(description="Generate and execute Table 1 for Enesort")
    parser.add_argument("--run", action="store_true", help="Run fresh benchmark execution live")
    parser.add_argument("--trials", type=int, default=5, help="Number of trials per cell for live execution (default: 5)")
    parser.add_argument("--latex", action="store_true", help="Print LaTeX table format")
    args = parser.parse_args()

    if args.run:
        pivot = run_live_benchmark(trials=args.trials)
    else:
        pivot = load_from_summary()

    if args.latex:
        print_table_latex(pivot)
    else:
        print_table_markdown(pivot)

if __name__ == "__main__":
    main()
