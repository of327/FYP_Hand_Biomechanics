# Dual LSM9DS1 (Arduino Uno) — Wiring & First steps

Overview
- This guide assumes two LSM9DS1 breakout boards connected to an Arduino Uno on the same I2C bus.

Wiring (Option A — using SDO/SA0 to set different addresses)
- Power: connect each IMU `VCC` to the Uno `3.3V` pin (or `5V` only if the breakout explicitly supports 5V I/O). Connect both `GND` pins to Uno `GND`.
- I2C: connect both IMU `SDA` pins to Uno `A4` and both `SCL` pins to Uno `A5`.
- Address select (SDO/SA0): locate the small pad or pin labelled `SDO`, `SA0`, or similar on each breakout. Tie one board's SDO to `GND` and the other board's SDO to `VCC` (3.3V). This makes the two boards use different I2C addresses.
- Pull-ups: most breakouts include I2C pull-ups; if not, add 4.7k resistors from SDA and SCL to 3.3V.

How to use the scanner
1. Open `DualIMU_I2C_Scanner.ino` in Arduino IDE.
2. Upload to your Uno.
3. Open Serial Monitor at `115200` baud.
4. Observe the reported I2C addresses. Note the addresses (hex and decimal).

Next steps after scanning
- If you see two distinct addresses, tell me the addresses and I'll provide a ready-to-upload sketch that uses the Adafruit (or SparkFun) LSM9DS1 library and reads accel/gyro/mag from both devices, printing CSV lines: `millis(),id,ax,ay,az,gx,gy,gz,mx,my,mz`.
- If you only see one address, re-check SDO wiring or use a TCA9548A I2C multiplexer (I can provide wiring and a sketch for that).

Notes & safety
- Prefer powering the IMU from `3.3V` to ensure 3.3V I/O levels. If powering from `5V`, confirm the breakout's I/O is 5V-tolerant before connecting SDA/SCL to the Uno.
- If your breakout exposes separate SDO pins for the accelerometer/gyro and the magnetometer, consult the breakout's silkscreen or datasheet and set the appropriate pad(s).
