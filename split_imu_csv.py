#!/usr/bin/env python3
"""split_imu_csv.py

Split an IMU logger CSV into two files: rows with `id==1` and `id==2`.

Usage:
  python split_imu_csv.py [path/to/file.csv] [--outdir DIR] [--overwrite]

If no path is provided the script will let you choose from recent CSVs in the
current directory (same selector style as `imu_analysis.py`).
"""

import argparse
import glob
import os
import pandas as pd


def load_data(path):
    try:
        df = pd.read_csv(path)
    except Exception:
        # try without header
        df = pd.read_csv(path, header=None)
    expected = ['millis','id','ax','ay','az','gx','gy','gz','mx','my','mz']
    if not all(c in df.columns for c in expected):
        if df.shape[1] >= 11:
            df = df.iloc[:, :11]
            df.columns = expected
        else:
            raise ValueError('CSV does not have expected columns')
    return df


def choose_file():
    candidates = sorted(glob.glob('imu_log*.csv'), reverse=True)
    if not candidates:
        candidates = sorted(glob.glob('*.csv'), reverse=True)
    if not candidates:
        raise FileNotFoundError('No CSV files found in current directory')
    print('Select a file to split:')
    for i, fname in enumerate(candidates[:20], 1):
        print(f'{i}: {fname}')
    choice = input('Enter number (or full path): ').strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx]
        else:
            raise ValueError('Invalid selection')
    return choice


def confirm_overwrite(path):
    if not os.path.exists(path):
        return True
    ans = input(f'File {path} exists. Overwrite? [y/N]: ').strip().lower()
    return ans == 'y'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('csv', nargs='?', help='Path to imu CSV file (optional)')
    p.add_argument('--outdir', help='Directory to write output files (default: same as CSV)')
    p.add_argument('--overwrite', action='store_true', help='Overwrite existing output files without prompting')
    args = p.parse_args()

    csv_path = args.csv
    if not csv_path:
        try:
            csv_path = choose_file()
        except Exception as e:
            print(e)
            return

    if not os.path.isfile(csv_path):
        print('CSV path not found:', csv_path)
        return

    try:
        df = load_data(csv_path)
    except Exception as e:
        print('Failed to read CSV:', e)
        return

    df1 = df[df['id'] == 1]
    df2 = df[df['id'] == 2]

    out_dir = args.outdir or os.path.dirname(csv_path) or '.'
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(csv_path))[0]

    out1 = os.path.join(out_dir, f"{stem}_id1.csv")
    out2 = os.path.join(out_dir, f"{stem}_id2.csv")

    if not args.overwrite:
        if not confirm_overwrite(out1):
            print('Skipping write to', out1)
            out1 = None
        if not confirm_overwrite(out2):
            print('Skipping write to', out2)
            out2 = None

    if out1:
        df1.to_csv(out1, index=False)
        print(f'Wrote {len(df1)} rows to {out1}')
    else:
        print('Did not write IMU1 file')

    if out2:
        df2.to_csv(out2, index=False)
        print(f'Wrote {len(df2)} rows to {out2}')
    else:
        print('Did not write IMU2 file')


if __name__ == '__main__':
    main()
