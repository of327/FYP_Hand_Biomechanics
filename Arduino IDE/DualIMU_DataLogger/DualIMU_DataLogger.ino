// DualIMU_DataLogger.ino
// Logs CSV lines for two LSM9DS1 IMUs using Adafruit_LSM9DS1 library.
// Replace the AG/M addresses below with the addresses your scanner printed.

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_LSM9DS1.h>

// --- ADDRESS CONFIGURATION ---
// Replace these with the addresses printed by the I2C scanner (hex),
// for each board: AG (accelerometer+gyro) and M (magnetometer).
// Typical LSM9DS1 default pairs are AG=0x6A/0x6B and M=0x1C/0x1E.
const uint8_t AG1_ADDR = 0x6B; // <--- set AG address for IMU 1
const uint8_t M1_ADDR  = 0x1E; // <--- set M address for IMU 1

const uint8_t AG2_ADDR = 0x6A; // <--- set AG address for IMU 2
const uint8_t M2_ADDR  = 0x1C; // <--- set M address for IMU 2

Adafruit_LSM9DS1 imu1 = Adafruit_LSM9DS1();
Adafruit_LSM9DS1 imu2 = Adafruit_LSM9DS1();
bool imu1_ok = false;
bool imu2_ok = false;
bool loggingEnabled = false;
// Optional button to toggle logging. Set to -1 to disable.
const int BUTTON_PIN = 2; // change to your pin or -1 to disable
int lastButtonState = LOW;
unsigned long lastDebounce = 0;
const unsigned long debounceDelay = 50;

void setup() {
  Serial.begin(115200);
  while (!Serial) ;
  Serial.println("Dual LSM9DS1 CSV logger");
  Wire.begin();

  // Prefer to initialize each LSM9DS1 instance with explicit AG/M addresses
  // so the library binds each object to the intended physical device.
  // Replace AGx_ADDR/Mx_ADDR above with the addresses printed by the scanner.
  imu1_ok = imu1.begin(AG1_ADDR, M1_ADDR);
  imu2_ok = imu2.begin(AG2_ADDR, M2_ADDR);

  if (!imu1_ok) {
    Serial.println("Warning: IMU1 not found at provided addresses.");
  } else {
    Serial.println("IMU1 initialized.");
    imu1.setupAccel(imu1.LSM9DS1_ACCELRANGE_2G);
    imu1.setupGyro(imu1.LSM9DS1_GYROSCALE_245DPS);
    imu1.setupMag(imu1.LSM9DS1_MAGGAIN_4GAUSS);
  }

  if (!imu2_ok) {
    Serial.println("Warning: IMU2 not found at provided addresses.");
  } else {
    Serial.println("IMU2 initialized.");
    imu2.setupAccel(imu2.LSM9DS1_ACCELRANGE_2G);
    imu2.setupGyro(imu2.LSM9DS1_GYROSCALE_245DPS);
    imu2.setupMag(imu2.LSM9DS1_MAGGAIN_4GAUSS);
  }

  Serial.println("CSV format: millis,id,ax,ay,az,gx,gy,gz,mx,my,mz");
  Serial.println("Controls: send 's' to START, 'p' to PAUSE, 't' to TOGGLE");
  if (BUTTON_PIN >= 0) {
    pinMode(BUTTON_PIN, INPUT_PULLUP); // assumes button to GND
    lastButtonState = digitalRead(BUTTON_PIN);
    Serial.println("Button toggle enabled on pin ");
  }
}

void loop() {
  unsigned long t = millis();

  // Serial control: s=start, p=pause, t=toggle
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 's') {
      loggingEnabled = true;
      Serial.println("Logging STARTED");
    } else if (c == 'p') {
      loggingEnabled = false;
      Serial.println("Logging PAUSED");
    } else if (c == 't') {
      loggingEnabled = !loggingEnabled;
      Serial.print("Logging "); Serial.println(loggingEnabled?"ENABLED":"DISABLED");
    }
  }

  // Button toggle (if enabled)
  if (BUTTON_PIN >= 0) {
    int reading = digitalRead(BUTTON_PIN);
    if (reading != lastButtonState) {
      lastDebounce = t;
    }
    if ((t - lastDebounce) > debounceDelay) {
      if (reading != lastButtonState) {
        lastButtonState = reading;
        if (reading == LOW) { // button pressed (active low)
          loggingEnabled = !loggingEnabled;
          Serial.print("Logging "); Serial.println(loggingEnabled?"ENABLED":"DISABLED");
        }
      }
    }
  }

  // IMU1
  if (loggingEnabled && imu1_ok) {
    sensors_event_t a, m, g, temp;
    imu1.getEvent(&a, &m, &g, &temp);
    printCSV_values(t, 1,
                    a.acceleration.x, a.acceleration.y, a.acceleration.z,
                    g.gyro.x, g.gyro.y, g.gyro.z,
                    m.magnetic.x, m.magnetic.y, m.magnetic.z);
  }

  // IMU2
  if (loggingEnabled && imu2_ok) {
    sensors_event_t a, m, g, temp;
    imu2.getEvent(&a, &m, &g, &temp);
    printCSV_values(t, 2,
                    a.acceleration.x, a.acceleration.y, a.acceleration.z,
                    g.gyro.x, g.gyro.y, g.gyro.z,
                    m.magnetic.x, m.magnetic.y, m.magnetic.z);
  }

  // Adjust delay to control sample rate (e.g., 20ms -> 50Hz)
  delay(20);
}

void printCSV_values(unsigned long t, int id,
                     float ax, float ay, float az,
                     float gx, float gy, float gz,
                     float mx, float my, float mz) {
  Serial.print(t); Serial.print(',');
  Serial.print(id); Serial.print(',');
  Serial.print(ax, 6); Serial.print(',');
  Serial.print(ay, 6); Serial.print(',');
  Serial.print(az, 6); Serial.print(',');
  Serial.print(gx, 6); Serial.print(',');
  Serial.print(gy, 6); Serial.print(',');
  Serial.print(gz, 6); Serial.print(',');
  Serial.print(mx, 6); Serial.print(',');
  Serial.print(my, 6); Serial.print(',');
  Serial.println(mz, 6);
}
