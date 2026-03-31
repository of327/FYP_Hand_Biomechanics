#!/usr/bin/env python3
"""LSM9DS1_serial_logger.py

Improved serial logger for DualIMU_DataLogger Arduino sketch.

Features:
- Auto-detect serial port (or use --port)
- Sends start/stop/toggle commands from stdin to Arduino while owning the COM port
- Creates timestamped CSV files per recording session
- Converts Arduino absolute millis timestamps to a relative sample index starting at 1
- Suppresses startup noise by clearing initial serial buffer

Usage:
  python LSM9DS1_serial_logger.py --port COM3 --start-on-run

"""

import argparse
import datetime
import re
import sys
import threading
import time

import serial
import serial.tools.list_ports


CSV_RE = re.compile(r"^\d+,")
START_MARKERS = ("Logging ENABLED", "Logging STARTED")
STOP_MARKERS = ("Logging DISABLED", "Logging PAUSED")


def find_port(preferred=None):
    if preferred:
        return preferred
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    if len(ports) == 1:
        return ports[0].device
    for p in ports:
        desc = (p.description or '').lower()
        if 'arduino' in desc or 'ch340' in desc or 'usb serial' in desc:
            return p.device
    return ports[0].device


def make_filename(prefix):
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{ts}.csv"


def run_logger(port, baud, prefix, start_on_run, interactive=True, retry_open=False):
    # open serial
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print('Failed to open serial port', port, e)
        return

    print(f"Opened {port} @ {baud}")

    # small delay and flush to avoid boot messages being treated as data
    time.sleep(0.5)
    try:
        ser.reset_input_buffer()
    except Exception:
        pass

    logfile = None
    logging = False
    base_ms = None

    if start_on_run:
        try:
            ser.write(b's')
        except Exception:
            pass

    # stdin thread to send single-char commands to Arduino
    if interactive:
        def stdin_thread(s):
            print("Interactive: type 's' to START, 'p' to PAUSE, 't' to TOGGLE, Ctrl-C to quit")
            try:
                while True:
                    ch = sys.stdin.read(1)
                    if not ch:
                        break
                    ch = ch.strip()
                    if not ch:
                        continue
                    if ch in ('s', 'p', 't'):
                        try:
                            s.write(ch.encode())
                            print(f"> sent '{ch}'")
                        except Exception as e:
                            print('Send failed:', e)
            except Exception:
                pass

        threading.Thread(target=stdin_thread, args=(ser,), daemon=True).start()

    print('Waiting for start/stop from Arduino...')

    try:
        while True:
            raw = ser.readline().decode('utf-8', errors='replace').strip()
            if not raw:
                continue

            # handle START
            if any(m in raw for m in START_MARKERS):
                if not logging:
                    fname = make_filename(prefix)
                    logfile = open(fname, 'w', newline='')
                    logfile.write('millis,id,ax,ay,az,gx,gy,gz,mx,my,mz\n')
                    logging = True
                    base_ms = None
                    print('Logging started ->', fname)
                else:
                    print(raw)
                continue

            # handle STOP
            if any(m in raw for m in STOP_MARKERS):
                if logging and logfile:
                    logfile.close()
                    print('Logging stopped, saved file')
                    logfile = None
                logging = False
                base_ms = None
                continue

            # data lines while logging
            if logging and CSV_RE.match(raw):
                parts = raw.split(',')
                try:
                    ms = int(parts[0])
                except Exception:
                    continue
                if base_ms is None:
                    base_ms = ms
                    rel = 1
                else:
                    rel = (ms - base_ms) + 1
                    if rel < 1:
                        rel = 1
                parts[0] = str(rel)
                out = ','.join(parts)
                if logfile:
                    logfile.write(out + '\n')
                    logfile.flush()
                print(out)
                continue

            # non-csv/status messages: print only when logging
            if logging:
                print(raw)

    except KeyboardInterrupt:
        print('\nInterrupted')
    finally:
        try:
            if logfile:
                logfile.close()
        except Exception:
            pass
        try:
            ser.close()
        except Exception:
            pass
        print('Closed')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='Serial port, e.g. COM3')
    p.add_argument('--baud', type=int, default=115200)
    p.add_argument('--prefix', default='imu_log')
    p.add_argument('--start-on-run', action='store_true', help="send 's' on open")
    p.add_argument('--no-interactive', dest='interactive', action='store_false')
    args = p.parse_args()

    port = find_port(args.port)
    if not port:
        print('No serial ports found; connect board and try again')
        sys.exit(1)

    run_logger(port, args.baud, args.prefix, args.start_on_run, interactive=args.interactive)


if __name__ == '__main__':
    main()
