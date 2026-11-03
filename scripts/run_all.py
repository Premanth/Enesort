#!/usr/bin/env python3
"""
run_all.py  –  Orchestrate the full EcoSort v2 benchmark suite
Runs the built harness binary, handles timeouts, collects CSVs.
Linux / WSL / macOS.
"""

import argparse
import datetime
import os
import platform
import subprocess
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='EcoSort v2 full study runner')
    parser.add_argument('--build-dir',  default='build')
    parser.add_argument('--results-dir', default='results/raw')
    parser.add_argument('--smoke', action='store_true', help='Quick smoke run')
    parser.add_argument('--trials', type=int, default=30)
    parser.add_argument('--sizes', default='1000,10000,100000,1000000')
    parser.add_argument('--taskset', type=int, default=-1, help='CPU core to pin (-1=auto)')
    args = parser.parse_args()

    os.makedirs(args.results_dir, exist_ok=True)

    bench_bin = os.path.join(args.build_dir, 'bench')
    if platform.system() == 'Windows':
        bench_bin += '.exe'

    if not os.path.exists(bench_bin):
        print(f"ERROR: bench binary not found at {bench_bin}", file=sys.stderr)
        print("Run: cmake -B build && cmake --build build --config Release", file=sys.stderr)
        sys.exit(1)

    ts   = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out  = os.path.join(args.results_dir, f'run_{ts}.csv')

    cmd  = [bench_bin]
    if args.smoke: cmd.append('--smoke')
    cmd += ['--trials', str(args.trials)]
    cmd += ['--sizes',  args.sizes]

    # Linux CPU pinning
    if platform.system() == 'Linux':
        core = args.taskset if args.taskset >= 0 else 0
        cmd = ['taskset', '-c', str(core)] + cmd
        # Try setting performance governor
        try:
            subprocess.run(['cpupower', 'frequency-set', '-g', 'performance'],
                           capture_output=True, timeout=5)
        except Exception:
            pass

    print(f"Running: {' '.join(cmd)}")
    print(f"Output: {out}")

    with open(out, 'w') as f:
        ret = subprocess.call(cmd, stdout=f)

    if ret == 0:
        print(f"Done. Results in {out}")
    else:
        print(f"Harness exited with code {ret}", file=sys.stderr)
        sys.exit(ret)

if __name__ == '__main__':
    main()

