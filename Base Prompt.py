"""Complementary filter orientation estimate for two IMUs.

Usage:
- If `imu1.csv` and `imu2.csv` exist in the script directory, the script
  will read them. Each CSV should have columns: `time` (optional),
  `ax,ay,az,gx,gy,gz`. Gyroscope values are expected in degrees/second.
- If CSVs are not present, the script will generate simulated data.

Output: `orientation_diff.csv` with timestamped orientation differences in
degrees (roll, pitch, yaw) and the per-IMU orientations for reference.

Notes:
- Roll/pitch are computed from accelerometer for long-term reference and
  from gyroscope integration for short-term — combined via a complementary
  filter. Yaw is integrated from gyro z (no magnetometer provided), so it
  will drift over time.
"""

import csv
import math
import os
import random
from typing import List, Tuple, Optional


def accel_to_roll_pitch(ax: float, ay: float, az: float) -> Tuple[float, float]:
	# Returns roll, pitch in degrees computed from accelerometer
	roll = math.degrees(math.atan2(ay, az))
	pitch = math.degrees(math.atan2(-ax, math.sqrt(ay * ay + az * az)))
	return roll, pitch


def complementary_filter(prev: Tuple[float, float, float],
						 gyro: Tuple[float, float, float],
						 accel_angles: Tuple[float, float],
						 dt: float,
						 alpha: float) -> Tuple[float, float, float]:
	# prev: (roll, pitch, yaw) in degrees
	# gyro: (gx, gy, gz) in degrees/second
	# accel_angles: (roll_acc, pitch_acc) in degrees
	# alpha: filter coefficient (0..1) — higher favors gyro
	prev_roll, prev_pitch, prev_yaw = prev
	gx, gy, gz = gyro

	# Integrate gyro (degrees)
	roll_gyro = prev_roll + gx * dt
	pitch_gyro = prev_pitch + gy * dt
	yaw = prev_yaw + gz * dt

	# Complementary combine for roll and pitch
	roll = alpha * roll_gyro + (1 - alpha) * accel_angles[0]
	pitch = alpha * pitch_gyro + (1 - alpha) * accel_angles[1]

	return roll, pitch, yaw


def read_imu_csv(path: str) -> Optional[List[dict]]:
	if not os.path.exists(path):
		return None
	with open(path, newline='') as f:
		reader = csv.DictReader(f)
		rows = [r for r in reader]
		return rows


def parse_rows(rows: List[dict], default_dt: float = 0.01) -> List[Tuple[float, float, float, float, float, float, float]]:
	# Returns list of tuples: (t, ax, ay, az, gx, gy, gz)
	out = []
	last_t = 0.0
	for i, r in enumerate(rows):
		# flexible key names
		def get(k):
			return r.get(k) or r.get(k.lower()) or r.get(k.upper())

		t_str = get('time')
		if t_str is None or t_str == '':
			t = last_t + default_dt
		else:
			t = float(t_str)
		ax = float(get('ax') or get('accx') or 0.0)
		ay = float(get('ay') or get('accy') or 0.0)
		az = float(get('az') or get('accz') or 0.0)
		gx = float(get('gx') or get('gyrx') or 0.0)
		gy = float(get('gy') or get('gyry') or 0.0)
		gz = float(get('gz') or get('gyrz') or 0.0)
		out.append((t, ax, ay, az, gx, gy, gz))
		last_t = t
	return out


def simulate_imus(duration: float = 10.0, dt: float = 0.01) -> Tuple[List[Tuple], List[Tuple]]:
	# Generate two simulated IMU streams with slight orientation difference
	steps = int(duration / dt)
	imu1 = []
	imu2 = []
	# base orientation: small tilt
	base_roll = 5.0
	base_pitch = -3.0
	base_yaw = 10.0
	for i in range(steps):
		t = i * dt
		# small motion: sinusoidal wobble
		roll = base_roll + 2.0 * math.sin(2 * math.pi * 0.2 * t)
		pitch = base_pitch + 1.5 * math.cos(2 * math.pi * 0.15 * t)
		yaw = base_yaw + 5.0 * math.sin(2 * math.pi * 0.05 * t)

		# convert angles to accelerometer readings (approx):
		# assume gravity = 9.81 m/s^2 and small angles
		ax = -9.81 * math.sin(math.radians(pitch)) + random.gauss(0, 0.05)
		ay = 9.81 * math.sin(math.radians(roll)) + random.gauss(0, 0.05)
		az = 9.81 * math.cos(math.radians(roll)) * math.cos(math.radians(pitch)) + random.gauss(0, 0.05)

		# gyro rates (deg/s) approximate from derivative of angle
		# compute derivatives numerically
		if i == 0:
			gx = gy = gz = 0.0
		else:
			# small finite difference of the motion functions
			gx = 2.0 * 2 * math.pi * 0.2 * math.cos(2 * math.pi * 0.2 * t)
			gy = -1.5 * 2 * math.pi * 0.15 * math.sin(2 * math.pi * 0.15 * t)
			gz = 5.0 * 2 * math.pi * 0.05 * math.cos(2 * math.pi * 0.05 * t)

		imu1.append((t, ax, ay, az, gx, gy, gz))

		# imu2 is imu1 with a constant offset and a bit more noise
		ax2 = ax + random.gauss(0, 0.02)
		ay2 = ay + random.gauss(0, 0.02)
		az2 = az + random.gauss(0, 0.02)
		gx2 = gx + 0.1 + random.gauss(0, 0.2)
		gy2 = gy - 0.05 + random.gauss(0, 0.2)
		gz2 = gz + random.gauss(0, 0.2)
		imu2.append((t, ax2, ay2, az2, gx2, gy2, gz2))

	return imu1, imu2


def write_output(path: str, rows: List[dict]) -> None:
	if not rows:
		return
	keys = list(rows[0].keys())
	with open(path, 'w', newline='') as f:
		writer = csv.DictWriter(f, keys)
		writer.writeheader()
		for r in rows:
			writer.writerow(r)


def run(alpha: float = 0.98, dt_default: float = 0.01) -> None:
	imu1_rows = read_imu_csv('imu1.csv')
	imu2_rows = read_imu_csv('imu2.csv')

	if imu1_rows and imu2_rows:
		imu1 = parse_rows(imu1_rows, default_dt=dt_default)
		imu2 = parse_rows(imu2_rows, default_dt=dt_default)
	else:
		imu1, imu2 = simulate_imus(duration=10.0, dt=dt_default)

	n = min(len(imu1), len(imu2))
	if n == 0:
		print('No data to process.')
		return

	out_rows = []
	prev1 = (0.0, 0.0, 0.0)
	prev2 = (0.0, 0.0, 0.0)

	for i in range(n):
		t1, ax1, ay1, az1, gx1, gy1, gz1 = imu1[i]
		t2, ax2, ay2, az2, gx2, gy2, gz2 = imu2[i]
		t = t1 if t1 is not None else i * dt_default

		roll_acc1, pitch_acc1 = accel_to_roll_pitch(ax1, ay1, az1)
		roll_acc2, pitch_acc2 = accel_to_roll_pitch(ax2, ay2, az2)

		prev1 = complementary_filter(prev1, (gx1, gy1, gz1), (roll_acc1, pitch_acc1), dt_default, alpha)
		prev2 = complementary_filter(prev2, (gx2, gy2, gz2), (roll_acc2, pitch_acc2), dt_default, alpha)

		roll1, pitch1, yaw1 = prev1
		roll2, pitch2, yaw2 = prev2

		row = {
			'time': f'{t:.4f}',
			'roll_diff': f'{(roll1 - roll2):.4f}',
			'pitch_diff': f'{(pitch1 - pitch2):.4f}',
			'yaw_diff': f'{(yaw1 - yaw2):.4f}',
			'roll1': f'{roll1:.4f}',
			'pitch1': f'{pitch1:.4f}',
			'yaw1': f'{yaw1:.4f}',
			'roll2': f'{roll2:.4f}',
			'pitch2': f'{pitch2:.4f}',
			'yaw2': f'{yaw2:.4f}',
		}
		out_rows.append(row)

	write_output('orientation_diff.csv', out_rows)
	print('Wrote orientation_diff.csv with', len(out_rows), 'rows')


if __name__ == '__main__':
	run()