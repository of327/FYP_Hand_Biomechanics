#!/usr/bin/env python3
"""imu_analysis.py

Simple IMU data inspection tool.

Reads a CSV produced by the logger (header: millis,id,ax,ay,az,gx,gy,gz,mx,my,mz),
separates IMU 1 and IMU 2, and produces four plots:
- IMU 1 Accelerometer (ax,ay,az)
- IMU 1 Gyroscope (gx,gy,gz)
- IMU 2 Accelerometer
- IMU 2 Gyroscope

Usage:
  python imu_analysis.py path/to/imu_log.csv

Optional flags:
  --save  Save plotted figures as PNG files alongside the CSV.
"""

import argparse
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt


def load_data(path):
    # Try reading with header; fallback to default column names if no header
    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise
    # Ensure expected columns exist
    expected = ['millis','id','ax','ay','az','gx','gy','gz','mx','my','mz']
    if not all(c in df.columns for c in expected):
        # try reading without header
        df = pd.read_csv(path, header=None)
        if df.shape[1] >= 11:
            df = df.iloc[:, :11]
            df.columns = expected
        else:
            raise ValueError('CSV does not have expected columns')
    return df


def plot_series(x, y_vals, labels, title, save_path=None):
    plt.figure()
    for y, lbl in zip(y_vals, labels):
        plt.plot(x, y, label=lbl)
    plt.title(title)
    plt.legend()
    plt.xlabel('sample')
    # no units on y-axis as requested
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('csv', nargs='?', help='Path to imu CSV file (optional)')
    p.add_argument('--save', action='store_true', help='Save figures as PNG')
    args = p.parse_args()

    csv_path = args.csv
    if not csv_path:
        # list recent imu CSV files in cwd
        candidates = sorted(glob.glob('imu_log*.csv'), reverse=True)
        if not candidates:
            # fallback to any csv
            candidates = sorted(glob.glob('*.csv'), reverse=True)
        if not candidates:
            print('No CSV files found in current directory. Provide a path as argument.')
            return
        print('Select a file to analyze:')
        for i, fname in enumerate(candidates[:20], 1):
            print(f'{i}: {fname}')
        choice = input('Enter number (or full path): ').strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(candidates):
                csv_path = candidates[idx]
            else:
                print('Invalid selection'); return
        else:
            csv_path = choice

    df = load_data(csv_path)

    # use millis column as x; it is already converted to relative index by the logger
    x = df['millis']

    df1 = df[df['id'] == 1]
    df2 = df[df['id'] == 2]

    base_dir = os.path.dirname(csv_path)
    stem = os.path.splitext(os.path.basename(csv_path))[0]

    # IMU1 accelerometer and gyroscope
    if not df1.empty:
        plot_series(df1['millis'], [df1['ax'], df1['ay'], df1['az']], ['ax','ay','az'], 'IMU 1 Accelerometer',
                    os.path.join(base_dir, f"{stem}_imu1_accel.png") if args.save else None)
        plot_series(df1['millis'], [df1['gx'], df1['gy'], df1['gz']], ['gx','gy','gz'], 'IMU 1 Gyroscope',
                    os.path.join(base_dir, f"{stem}_imu1_gyro.png") if args.save else None)
    else:
        print('No data for IMU 1 in file')

    # IMU2 accelerometer and gyroscope
    if not df2.empty:
        plot_series(df2['millis'], [df2['ax'], df2['ay'], df2['az']], ['ax','ay','az'], 'IMU 2 Accelerometer',
                    os.path.join(base_dir, f"{stem}_imu2_accel.png") if args.save else None)
        plot_series(df2['millis'], [df2['gx'], df2['gy'], df2['gz']], ['gx','gy','gz'], 'IMU 2 Gyroscope',
                    os.path.join(base_dir, f"{stem}_imu2_gyro.png") if args.save else None)
    else:
        print('No data for IMU 2 in file')

    plt.show()


if __name__ == '__main__':
    main()
