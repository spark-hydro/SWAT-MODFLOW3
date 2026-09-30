#!/usr/bin/env python3
"""Regression check for SWAT-MODFLOW3.

Copies the dataset to a scratch folder, deletes its old outputs, runs the
executable there, and compares every numeric value in the new outputs with
the reference outputs shipped in the dataset (written by the Windows/Intel
build). The dataset itself is never modified.

    python3 scripts/regress.py build/release/swatmf3-*-Rel swatmf3-dataset

Exit code 0 = run finished and all files match within tolerance.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

NUM = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?')
# Files compared. mf_*.lst is left out on purpose: it embeds dates and timings.
PATTERNS = ['output.std', 'output.hru', 'output.rsv', 'output.sub', 'output.rch',
            'swatmf_out_*']


def numbers(path):
    with open(path, errors='ignore') as fh:
        return [float(t.replace('D', 'E').replace('d', 'e')) for t in NUM.findall(fh.read())]


def compare(ref, new, rtol, floor):
    """Return (n_values, max_rel_diff, n_over_tol), or None if counts differ."""
    a, b = numbers(ref), numbers(new)
    if len(a) != len(b):
        return None, len(a), len(b)
    worst, bad = 0.0, 0
    for x, y in zip(a, b):
        d = abs(x - y) / max(abs(x), abs(y), floor)
        worst = max(worst, d)
        bad += d > rtol
    return (len(a), worst, bad), len(a), len(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('exe', help='SWAT-MODFLOW3 executable')
    ap.add_argument('dataset', help='model folder with file.cio and reference outputs')
    ap.add_argument('--rtol', type=float, default=1e-3, help='max relative difference (default 1e-3)')
    ap.add_argument('--floor', type=float, default=1e-6, help='denominator floor for tiny values')
    ap.add_argument('--keep', action='store_true', help='keep the scratch run folder')
    args = ap.parse_args()

    exe, ref_dir = os.path.abspath(args.exe), os.path.abspath(args.dataset)
    if not os.path.isfile(exe):
        sys.exit(f'executable not found: {exe}')
    if not os.path.isfile(os.path.join(ref_dir, 'file.cio')):
        sys.exit(f'no file.cio in {ref_dir}')

    ref_files = sorted({os.path.basename(p) for pat in PATTERNS
                        for p in glob.glob(os.path.join(ref_dir, pat))})
    if not ref_files:
        sys.exit('no reference output files found in the dataset')

    run_dir = tempfile.mkdtemp(prefix='swatmf_regress_')
    try:
        print(f'run folder: {run_dir}')
        shutil.copytree(ref_dir, run_dir, dirs_exist_ok=True)
        # Linux is case-sensitive, Windows is not: add a lowercase copy of any
        # file whose name has capitals (e.g. Tmp1.Tmp -> tmp1.tmp).
        for name in os.listdir(run_dir):
            low = name.lower()
            if low != name and not os.path.exists(os.path.join(run_dir, low)):
                shutil.copy2(os.path.join(run_dir, name), os.path.join(run_dir, low))
        # Remove old outputs so a file that is not rewritten is caught.
        for name in ref_files:
            os.remove(os.path.join(run_dir, name))

        t0 = time.time()
        with open(os.path.join(run_dir, 'run.log'), 'w') as log:
            rc = subprocess.run([exe], cwd=run_dir, stdout=log, stderr=subprocess.STDOUT).returncode
        with open(os.path.join(run_dir, 'run.log'), errors='ignore') as fh:
            done = 'Execution successfully completed' in fh.read()
        print(f'run: exit {rc}, {time.time() - t0:.1f} s, '
              f'{"completed" if done else "DID NOT COMPLETE"}')

        failed = rc != 0 or not done
        print(f'\n{"file":38s} {"values":>8s} {"max rel diff":>13s}  result')
        for name in ref_files:
            new = os.path.join(run_dir, name)
            if not os.path.isfile(new):
                print(f'{name:38s} {"":8s} {"":13s}  FAIL (not written)')
                failed = True
                continue
            res, na, nb = compare(os.path.join(ref_dir, name), new, args.rtol, args.floor)
            if res is None:
                print(f'{name:38s} {na:8d} {"":13s}  FAIL (value count {na} vs {nb})')
                failed = True
            else:
                n, worst, bad = res
                ok = bad == 0
                failed |= not ok
                print(f'{name:38s} {n:8d} {worst:13.2e}  {"ok" if ok else f"FAIL ({bad} over {args.rtol:g})"}')
        print('\nPASSED' if not failed else '\nFAILED')
        if failed:
            args.keep = True
        return 1 if failed else 0
    finally:
        if args.keep:
            print(f'kept: {run_dir}')
        else:
            shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
