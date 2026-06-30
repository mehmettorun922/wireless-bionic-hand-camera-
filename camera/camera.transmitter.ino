#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#define CE_PIN  4
#define CSN_PIN 5
#define LED_PIN 2

RF24 radio(CE_PIN, CSN_PIN);
const byte address[6] = "00001";

// Gönderilecek payload — alıcı uint8_t[5] bekliyor
uint8_t payload[5] = {90, 90, 90, 90, 90};

// Son gönderilen değerler (verici tarafında yumuşatma)
uint8_t lastSent[5]    = {90, 90, 90, 90, 90};

// Verici tarafında maksimum adım sınırı (her gönderimde max bu kadar değişir)
// Python zaten yumuşatıyor, bu ek güvenlik katmanı
#define MAX_STEP 40

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  SPI.begin(18, 19, 23, CSN_PIN);
  delay(100);

  if (!radio.begin()) {
    Serial.println("[HATA] nRF24L01 baslatilamadi!");
    while (true) {
      digitalWrite(LED_PIN, HIGH); delay(150);
      digitalWrite(LED_PIN, LOW);  delay(150);
    }
  }

  radio.setPALevel(RF24_PA_MAX);
  radio.setDataRate(RF24_2MBPS);
  radio.setRetries(1, 3);
  radio.openWritingPipe(address);
  radio.stopListening();

  digitalWrite(LED_PIN, HIGH);
  Serial.println("[HAZIR] Verici aktif. Format: a0,a1,a2,a3,a4");
}

void loop() {
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim();
    if (incoming.length() == 0) return;

    int vals[5];
    if (sscanf(incoming.c_str(), "%d,%d,%d,%d,%d",
        &vals[0], &vals[1], &vals[2], &vals[3], &vals[4]) == 5) {

      for (int i = 0; i < 5; i++) {
        // 1) 0-180 kısıtı
        int v = constrain(vals[i], 0, 180);

        // 2) YÖN TERSİNE ÇEVİR — el kapandığında servo kapansın
        v = 180 - v;

        // 3) Rate limiting — ani sıçramaları önle
        int delta = v - (int)lastSent[i];
        if (delta >  MAX_STEP) v = lastSent[i] + MAX_STEP;
        if (delta < -MAX_STEP) v = lastSent[i] - MAX_STEP;

        payload[i]  = (uint8_t)constrain(v, 0, 180);
        lastSent[i] = payload[i];
      }

      bool ok = radio.write(&payload, sizeof(payload));

      if (ok) {
        Serial.printf("[OK] %d,%d,%d,%d,%d\n",
          payload[0], payload[1], payload[2], payload[3], payload[4]);
        digitalWrite(LED_PIN, LOW);  delay(10);
        digitalWrite(LED_PIN, HIGH);
      } else {
        Serial.println("[WARN] Gonderim basarisiz");
      }
    } else {
      Serial.printf("[WARN] Gecersiz format: '%s'\n", incoming.c_str());
    }
  }
}
