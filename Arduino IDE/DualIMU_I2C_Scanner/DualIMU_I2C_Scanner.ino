#define RUN_I2C_SCANNER

// DualIMU_I2C_Scanner.ino
// Scans the I2C bus and prints detected addresses.
// Use this after wiring both LSM9DS1 breakouts to A4/A5 (SDA/SCL),
// VCC to 3.3V (or 5V if breakout supports), and GND to GND.
// Tie one board's SDO to GND and the other's SDO to VCC to give
// them different I2C addresses before running this sketch.

#include <Wire.h>

// To avoid duplicate `setup()`/`loop()` when multiple .ino files are
// present in the same sketch, only enable the scanner when the
// `RUN_I2C_SCANNER` macro is defined (define it in the Arduino IDE
// build flags or at the top of this file to run the scanner).
#ifdef RUN_I2C_SCANNER
void setup() {
  Serial.begin(115200);
  while (!Serial) ;
  Serial.println("I2C Scanner - Dual LSM9DS1 setup");
  Wire.begin();
}

void loop() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Scanning...");

  for(address = 1; address < 127; address++ )
  {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0)
    {
      Serial.print("I2C device found at address 0x");
      if (address<16)
        Serial.print("0");
      Serial.print(address,HEX);
      Serial.print("  ");
      Serial.print(address,DEC);
      Serial.println(" ");

      nDevices++;
    }
    else if (error==4)
    {
      Serial.print("Unknown error at address 0x");
      if (address<16)
        Serial.print("0");
      Serial.println(address,HEX);
    }
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found. Check wiring and power.");
  else {
    Serial.print("Done. Devices found: ");
    Serial.println(nDevices);
  }

  Serial.println("---");
  delay(3000); // scan every 3 seconds
}
#endif // RUN_I2C_SCANNER
