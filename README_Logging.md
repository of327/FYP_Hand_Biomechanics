# Serial logging (Arduino + Python)

1) Install dependency:
```bash
pip install pyserial
```

2) Run Arduino sketch on the Uno (the `DualIMU_DataLogger.ino` in this folder).

3) Start the Python logger in the same folder. It will auto-detect the serial port if possible:
```bash
python serial_logger.py
```
If auto-detect fails, pass `--port COM3` (Windows) or `--port /dev/ttyACM0` (Linux).

4) Use the single physical button wired to the Arduino (default `BUTTON_PIN = 2`) to start/stop logging. When you press the button the Arduino prints `Logging ENABLED` and the Python script will create a new file `imu_log_YYYYMMDD_HHMMSS.csv`. Press again to stop and save.

5) Optional: start the Arduino logging from the Python script by using `--start-on-run` which sends `s` to the Arduino when the Python script opens the port.

Files created:
- `serial_logger.py` — the Python logger
- `imu_log_YYYYMMDD_HHMMSS.csv` — generated CSV files while logging
