#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

// CE ve CSN pinleri
#define CE_PIN 9
#define CSN_PIN 10
RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

// Flex sensör pinleri
#define FLEX_PIN1 A0
#define FLEX_PIN2 A1
#define FLEX_PIN3 A2
#define FLEX_PIN4 A3
#define FLEX_PIN5 A4

// Flex min - max (senin değerlerin)
#define FLEX_MIN1 2500
#define FLEX_MAX1 3000

#define FLEX_MIN2 3150
#define FLEX_MAX2 3400

#define FLEX_MIN3 2500
#define FLEX_MAX3 3200

#define FLEX_MIN4 3200
#define FLEX_MAX4 3400

#define FLEX_MIN5 3500
#define FLEX_MAX5 3800

int flexValue1, servoValue1;
int flexValue2, servoValue2;
int flexValue3, servoValue3;
int flexValue4, servoValue4;
int flexValue5, servoValue5;

void setup() {
  Serial.begin(9600);

  if (!radio.begin()) {
    Serial.println("nRF24 baslatilamadi!");
    while (1);
  }

  radio.openWritingPipe(address);
  radio.setPALevel(RF24_PA_MAX);
  radio.setDataRate(RF24_2MBPS);
  radio.setRetries(3, 5);
  radio.stopListening();
  Serial.println("Verici hazir (5 flex)...");
  Serial.println("FORMAT: FLEX -> SERVO");
}

void loop() {
  // Flex oku (HAM)
  flexValue1 = analogRead(FLEX_PIN1);
  flexValue2 = analogRead(FLEX_PIN2);
  flexValue3 = analogRead(FLEX_PIN3);
  flexValue4 = analogRead(FLEX_PIN4);
  flexValue5 = analogRead(FLEX_PIN5);

  // Servo açıları
  servoValue1 = constrain(map(flexValue1, FLEX_MIN1, FLEX_MAX1, 0, 180), 0, 180);
  servoValue2 = constrain(map(flexValue2, FLEX_MIN2, FLEX_MAX2, 0, 180), 0, 180);
  servoValue3 = constrain(map(flexValue3, FLEX_MIN3, FLEX_MAX3, 0, 180), 0, 180);
  servoValue4 = constrain(map(flexValue4, FLEX_MIN4, FLEX_MAX4, 0, 180), 0, 180);
  servoValue5 = constrain(map(flexValue5, FLEX_MIN5, FLEX_MAX5, 0, 180), 0, 180);

  // Gönder
  uint8_t data[5] = {
    servoValue1,
    servoValue2,
    servoValue3,
    servoValue4,
    servoValue5
  };
  
  bool ok = radio.write(&data, sizeof(data));

  // SERIAL MONITOR CIKTISI
  Serial.print("F1: "); Serial.print(flexValue1);
  Serial.print(" -> S1: "); Serial.println(servoValue1);
  Serial.print("F2: "); Serial.print(flexValue2);
  Serial.print(" -> S2: "); Serial.println(servoValue2);
  Serial.print("F3: "); Serial.print(flexValue3);
  Serial.print(" -> S3: "); Serial.println(servoValue3);
  Serial.print("F4: "); Serial.print(flexValue4);
  Serial.print(" -> S4: "); Serial.println(servoValue4);
  Serial.print("F5: "); Serial.print(flexValue5);
  Serial.print(" -> S5: "); Serial.println(servoValue5);

  Serial.println(ok ? " (OK)" : " (HATA)");
  delay(50);
}