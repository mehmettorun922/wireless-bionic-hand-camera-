#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#include <ESP32Servo.h> // ESP32 için servo kütüphanesi

#define CE_PIN 22
#define CSN_PIN 21

// 5 servo için pinler
#define SERVO1_PIN 13
#define SERVO2_PIN 14
#define SERVO3_PIN 25
#define SERVO4_PIN 26
#define PIN_SERVO5 27 // Görseldeki tanım: #define SERVO5_PIN 27

RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

Servo myServo1;
Servo myServo2;
Servo myServo3;
Servo myServo4;
Servo myServo5;

// Flex sensörlerden gelen veriler
uint8_t gelenVeri1; // 1. flex sensör
uint8_t gelenVeri2; // 2. flex sensör
uint8_t gelenVeri3; // 3. flex sensör
uint8_t gelenVeri4; // 4. flex sensör
uint8_t gelenVeri5; // 5. flex sensör

void setup() {
  Serial.begin(115200);

  // Servoları başlat
  myServo1.attach(SERVO1_PIN);
  myServo2.attach(SERVO2_PIN);
  myServo3.attach(SERVO3_PIN);
  myServo4.attach(SERVO4_PIN);
  myServo5.attach(PIN_SERVO5);

  // nRF24 başlat
  SPI.begin(18, 19, 23); // SCK, MISO, MOSI pinleri
  if (!radio.begin()) {
    Serial.println("nRF24 baslatilamadi!");
    while (1);
  }

  radio.openReadingPipe(0, address);
  radio.setPALevel(RF24_PA_MAX); // daha güçlü sinyal
  radio.setDataRate(RF24_2MBPS); // hızlı ve düşük gecikmeli
  radio.startListening();

  Serial.println("Alici hazir, 5 flex sensör ile 5 servo kontrol ediliyor...");
}

void loop() {
  if (radio.available()) {
    // 5 flex sensör verisini al
    uint8_t gelenVeriler[5];
    radio.read(&gelenVeriler, sizeof(gelenVeriler));

    gelenVeri1 = gelenVeriler[0];
    gelenVeri2 = gelenVeriler[1];
    gelenVeri3 = gelenVeriler[2];
    gelenVeri4 = gelenVeriler[3];
    gelenVeri5 = gelenVeriler[4];

    Serial.print("Flex1: "); Serial.println(gelenVeri1);
    Serial.print("Flex2: "); Serial.println(gelenVeri2);
    Serial.print("Flex3: "); Serial.println(gelenVeri3);
    Serial.print("Flex4: "); Serial.println(gelenVeri4);
    Serial.print("Flex5: "); Serial.println(gelenVeri5);

    // 1. flex -> Servo1
    myServo1.write(gelenVeri1);

    // 2. flex -> Servo2
    myServo2.write(gelenVeri2);

    // 3. flex -> Servo3
    myServo3.write(gelenVeri3);

    // 4. flex -> Servo4
    myServo4.write(gelenVeri4);

    // 5. flex -> Servo5
    myServo5.write(gelenVeri5);
  }
}