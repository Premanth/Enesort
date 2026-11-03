#!/usr/bin/env python3
"""
run_experiments.py  –  Orchestrates all 6 experimental studies for Enesort,
produces all raw CSVs, statistical analyses, LaTeX/Markdown tables,
publication vector PDF plots, and RESULTS_SUMMARY.md.
"""

import os
import sys
import subprocess
import platform
import datetime
import argparse

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(PROJ_DIR, "build_manual")
RAW_DIR = os.path.join(PROJ_DIR, "results", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

BENCH_EXE = os.path.join(BIN_DIR, "bench.exe" if platform.system() == "Windows" else "bench")
COUNTER_EXE = os.path.join(BIN_DIR, "counter_study.exe" if platform.system() == "Windows" else "counter_study")

ENV = os.environ.copy()
if "msys" not in ENV.get("PATH", "").lower():
    ENV["PATH"] = r"C:\msys64\ucrt64\bin;" + ENV.get("PATH", "")

def run_cmd_capture(cmd, desc):
    print(f"  -> Running {desc}...", flush=True)
    t0 = datetime.datetime.now()
    res = subprocess.run(cmd, env=ENV, capture_output=True, text=True)
    t1 = datetime.datetime.now()
    if res.returncode != 0:
        print(f"ERROR in {desc}! Exit code: {res.returncode}", flush=True)
        print(res.stderr, flush=True)
        sys.exit(res.returncode)
    lines = res.stdout.strip().splitlines()
    header = lines[0] if lines else ""
    data_lines = [line for line in lines[1:] if line.strip() and not line.startswith("timestamp,")]
    dur = (t1 - t0).total_seconds()
    print(f"     [OK] {len(data_lines)} records in {dur:.2f}s", flush=True)
    return header, data_lines

def append_to_csv(out_csv, header, data_lines):
    file_exists = os.path.exists(out_csv) and os.path.getsize(out_csv) > 0
    with open(out_csv, "a", encoding="utf-8") as f:
        if not file_exists and header:
            f.write(header + "\n")
        for line in data_lines:
            f.write(line + "\n")
        f.flush()

def run_study1(trials, sizes_str):
    out_csv = os.path.join(RAW_DIR, "study1_main.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    print(f"\n========================================================")
    print(f"Study 1: Main Comparison (trials={trials}, sizes={sizes_str})")
    print(f"========================================================")

    algo_types = [
        ("enesort",       "int32"),
        ("std_sort",      "int32"),
        ("stable_sort",   "int32"),
        ("std_precheck",  "int32"),
        ("heapsort",      "int32"),
        ("mo3_quicksort", "int32"),
        ("yaroslavskiy",  "int32"),
        ("mergesort",     "int32"),
        ("pdqsort",       "int32"),
        ("ips4o",         "int32"),
        ("timsort",       "int32"),
        ("enesort",       "int64"),
        ("std_sort",      "int64"),
        ("pdqsort",       "int64"),
        ("enesort",       "double"),
        ("std_sort",      "double"),
        ("pdqsort",       "double"),
        ("enesort",       "kvpair"),
        ("std_sort",      "kvpair"),
        ("pdqsort",       "kvpair")
    ]

    for algo, type_ in algo_types:
        cmd = [BENCH_EXE, "--study", "main", "--algo", algo, "--type", type_,
               "--trials", str(trials), "--sizes", sizes_str]
        header, data = run_cmd_capture(cmd, f"{algo} ({type_})")
        append_to_csv(out_csv, header, data)

def run_study2(trials, sizes_str):
    out_csv = os.path.join(RAW_DIR, "study2_ablation.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    print(f"\n========================================================")
    print(f"Study 2: Ablation Study (trials={trials}, sizes={sizes_str})")
    print(f"========================================================")

    ablation_algos = [
        "enesort", "enesort_no_f1", "enesort_no_f2", "enesort_no_f3", "enesort_no_f4",
        "mo3_quicksort", "std_sort"
    ]
    for algo in ablation_algos:
        cmd = [BENCH_EXE, "--study", "ablation", "--algo", algo, "--type", "int32",
               "--trials", str(trials), "--sizes", sizes_str]
        header, data = run_cmd_capture(cmd, f"Ablation: {algo}")
        append_to_csv(out_csv, header, data)

def run_study3(trials, sizes_str):
    out_csv = os.path.join(RAW_DIR, "study3_cutoff.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    print(f"\n========================================================")
    print(f"Study 3: Insertion Cutoff Sweep (trials={trials}, sizes={sizes_str})")
    print(f"========================================================")

    cutoff_algos = [
        "enesort_cutoff_8", "enesort_cutoff_12", "enesort_cutoff_16",
        "enesort_cutoff_24", "enesort_cutoff_32", "enesort_cutoff_48",
        "enesort_cutoff_64", "enesort_cutoff_96", "enesort_cutoff_128"
    ]
    for algo in cutoff_algos:
        cmd = [BENCH_EXE, "--study", "cutoff", "--algo", algo, "--type", "int32",
               "--trials", str(trials), "--sizes", sizes_str]
        header, data = run_cmd_capture(cmd, f"Cutoff: {algo}")
        append_to_csv(out_csv, header, data)

def run_study4(trials, sizes_str):
    out_csv = os.path.join(RAW_DIR, "study4_pivot.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    print(f"\n========================================================")
    print(f"Study 4: Pivot-Sampling & Skew (trials={trials}, sizes={sizes_str})")
    print(f"========================================================")

    pivot_algos = [
        "enesort_sample_3", "enesort_sample_5", "enesort_sample_7",
        "enesort_sample_9", "enesort_sample_skew"
    ]
    for algo in pivot_algos:
        cmd = [BENCH_EXE, "--study", "pivot", "--algo", algo, "--type", "int32",
               "--trials", str(trials), "--sizes", sizes_str]
        header, data = run_cmd_capture(cmd, f"Pivot sample: {algo}")
        append_to_csv(out_csv, header, data)

def run_study5(trials, sizes_str):
    out_csv = os.path.join(RAW_DIR, "study5_worstcase.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    print(f"\n========================================================")
    print(f"Study 5: Worst-Case Killer Sequence (trials={trials})")
    print(f"========================================================")

    cmd = [BENCH_EXE, "--study", "worstcase", "--type", "int32",
           "--trials", str(trials), "--sizes", sizes_str]
    header, data = run_cmd_capture(cmd, "Worst-case killer study")
    append_to_csv(out_csv, header, data)

def run_study6():
    out_csv = os.path.join(RAW_DIR, "study6_counters.csv")
    if os.path.exists(out_csv):
        os.remove(out_csv)
    print(f"\n========================================================")
    print(f"Study 6: Operational Step Counters Study")
    print(f"========================================================")

    cmd = [COUNTER_EXE]
    header, data = run_cmd_capture(cmd, "Counters study")
    append_to_csv(out_csv, header, data)

def run_analysis_pipeline():
    print(f"\n========================================================")
    print(f"Running Analysis, Tables, Figures, and Summary Pipeline")
    print(f"========================================================")

    # 1. analyze.py
    subprocess.run([sys.executable, "-u", os.path.join(PROJ_DIR, "scripts", "analyze.py")], check=True)

    # 2. tables.py
    subprocess.run([sys.executable, "-u", os.path.join(PROJ_DIR, "scripts", "tables.py")], check=True)

    # 3. plots.py
    subprocess.run([sys.executable, "-u", os.path.join(PROJ_DIR, "scripts", "plots.py")], check=True)

    # 4. generate_results_summary.py
    subprocess.run([sys.executable, "-u", os.path.join(PROJ_DIR, "scripts", "generate_results_summary.py"), "results"], check=True)

    print(f"\nAll studies, tables, and figures generated successfully!", flush=True)

def main():
    parser = argparse.ArgumentParser(description="Enesort benchmark suite")
    parser.add_argument("--trials", type=int, default=10, help="Number of trials per cell (default: 10)")
    parser.add_argument("--sizes", default="1000,10000,100000,1000000", help="Sizes for main comparison")
    parser.add_argument("--sizes-sub", default="10000,100000,1000000", help="Sizes for sub-studies")
    args = parser.parse_args()

    t_start = datetime.datetime.now()

    run_study1(args.trials, args.sizes)
    run_study2(args.trials, args.sizes_sub)
    run_study3(args.trials, args.sizes_sub)
    run_study4(args.trials, args.sizes_sub)
    run_study5(args.trials, args.sizes)
    run_study6()

    run_analysis_pipeline()

    t_end = datetime.datetime.now()
    total_time = (t_end - t_start).total_seconds()
    print(f"\n>>> Total benchmark and analysis pipeline completed in {total_time:.1f}s ({total_time/60:.1f} min)")

if __name__ == "__main__":
    main()
