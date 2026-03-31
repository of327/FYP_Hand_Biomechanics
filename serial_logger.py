#!/usr/bin/env python3
"""Serial logger for DualIMU Arduino sketch.

Listens to the Arduino serial port, waits for the Arduino to announce
"Logging ENABLED" / "Logging DISABLED" (or STARTED/PAUSED), and
creates a new CSV file for each logging session. Filters out non-CSV
lines and writes only true data lines to the file.

Usage:
  python serial_logger.py --port COM3
  python serial_logger.py           # attempts to auto-detect a single serial port

Options:
  --port   Serial port to use (e.g. COM3 or /dev/ttyACM0)
  --baud   Baud rate (default 115200)
  --prefix Filename prefix (default imu_log)
  --start-on-run  Send 's' to Arduino at start to request logging
"""

import argparse
import serial
import serial.tools.list_ports
import re
import threading
import time
import datetime
import sys
import threading


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
    # try to find an Arduino-like device
    for p in ports:
        if 'Arduino' in (p.description or '') or 'CH340' in (p.description or ''):
            return p.device
    # fall back to the first
    return ports[0].device


def make_filename(prefix):
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{ts}.csv"


def run_logger(port, baud, prefix, start_on_run, interactive=True):
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print('Failed to open serial port', port, e)
        return

    print('Opened', port, 'at', baud)
    logfile = None
    logging = False
    base_ms = None

    if start_on_run:
        try:
            ser.write(b's')
        except Exception:
            pass

    # give Arduino time to reboot/settle and clear any buffered startup lines
    time.sleep(0.5)
    try:
        ser.reset_input_buffer()
    except Exception:
        pass

    # interactive stdin control (send 's','p','t' to Arduino)
    
    if interactive:
        def stdin_sender(ser):
            print("Type 's' to START, 'p' to PAUSE, 't' to TOGGLE (Ctrl-C to quit)")
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
                            ser.write(ch.encode())
                            print(f"> sent '{ch}'")
                        except Exception as e:
                            print('Failed to send command:', e)
            except Exception:
                pass

        threading.Thread(target=stdin_sender, args=(ser,), daemon=True).start()

    try:
        print('Waiting for logging commands from Arduino...')
        while True:
            raw = ser.readline().decode('utf-8', errors='replace').strip()
            if not raw:
                continue

            # detect start markers
            if any(m in raw for m in START_MARKERS):
                if not logging:
                    fname = make_filename(prefix)
                    logfile = open(fname, 'w', newline='')
                    logfile.write('millis,id,ax,ay,az,gx,gy,gz,mx,my,mz\n')
                    logging = True
                    base_ms = None
                    print('Logging started ->', fname)
                else:
                    # already logging: print status
                    print(raw)
                continue

            # detect stop markers
            if any(m in raw for m in STOP_MARKERS):
                if logging and logfile:
                    logfile.close()
                    print('Logging stopped, saved file')
                    logfile = None
                logging = False
                base_ms = None
                continue

            # CSV data: only process while logging
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
                out_line = ','.join(parts)
                if logfile:
                    logfile.write(out_line + '\n')
                    logfile.flush()
                print(out_line)
                continue

            # non-CSV, non-status messages: print only when logging
            if logging:
                print(raw)

    except KeyboardInterrupt:
        print('\nInterrupted by user')
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


# Note: stdin thread is started from inside run_logger to ensure the
# serial port (`ser`) is available in that scope.


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', help='Serial port (e.g. COM3 or /dev/ttyACM0)')
    p.add_argument('--baud', type=int, default=115200)
    p.add_argument('--prefix', default='imu_log')
    p.add_argument('--start-on-run', action='store_true', help="Send 's' to Arduino at start")
    args = p.parse_args()

    port = find_port(args.port)
    if not port:
        print('No serial ports found. Connect Arduino and try again.')
        sys.exit(1)

    run_logger(port, args.baud, args.prefix, args.start_on_run)


if __name__ == '__main__':
    main()
