#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Wire.h>

const char* ssid = "TurkNet";
const char* password = "Seccad.*0805";

// Google Cloud Firebase Veritabanı Adresin
const char* firebaseHost = "akilli-kask-proje-default-rtdb.europe-west1.firebasedatabase.app";

class TinyLCD {
  uint8_t addr;
public:
  TinyLCD(uint8_t lcd_addr) { addr = lcd_addr; }
  void begin() {
    delay(50);
    command(0x03); command(0x03); command(0x03); command(0x02);
    command(0x28); command(0x0C); command(0x06);
    clear();
  }
  void send(uint8_t value, uint8_t mode) {
    uint8_t high = mode | (value & 0xF0) | 0x08;
    uint8_t low = mode | ((value << 4) & 0xF0) | 0x08;
    Wire.beginTransmission(addr);
    Wire.write(high | 0x04); Wire.write(high & ~0x04);
    Wire.write(low | 0x04); Wire.write(low & ~0x04);
    Wire.endTransmission();
    delayMicroseconds(50);
  }
  void command(uint8_t val) { send(val, 0x00); }
  void writeChar(uint8_t val) { send(val, 0x01); }
  void clear() { command(0x01); delay(2); }
  void setCursor(uint8_t col, uint8_t row) {
    int row_offsets[] = { 0x00, 0x40, 0x14, 0x54 };
    command(0x80 | (col + row_offsets[row]));
  }
  void print(const String &s) {
    for (int i = 0; i < s.length(); i++) {
      writeChar(s[i]);
    }
  }
};

TinyLCD lcd(0x27);

#ifndef D1
#define D1 1
#endif
#ifndef D2
#define D2 2
#endif

const int sosButtonPin = D1; 
const int buzzerPin = D2;     // Sesli uyarı için Buzzer pini
const int dumanI2CAddress = 0x39;

float ivmeX = 1.0;
int dumanDegeri = 180;
bool lastButtonState = HIGH;
bool sosToggleState = false;
int sosDurumuVal = 0;

// Örnek Harita Koordinatları (Van Merkez)
float latVal = 38.5023;
float lonVal = 43.3820;

unsigned long sonGonderimZamani = 0;
const unsigned long gonderimAraligi = 3000;

void setup() {
  Serial.begin(57600);
  delay(500);

  Wire.begin();
  pinMode(sosButtonPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);

  lcd.begin();
  lcd.setCursor(0, 0);
  lcd.print("Google Cloud Bag.");

  WiFi.begin(ssid, password);
  
  int deneme = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    deneme++;
    if (deneme > 30) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("WiFi Hata");
      return; 
    }
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Bulut Baglanti OK");
  delay(2000);
}

void firebaseVeriyiGonder(float ivme, int duman, int sos, float lat, float lon) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure();
    
    HTTPClient http;
    String url = "https://" + String(firebaseHost) + "/telemetri.json";
    
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    String payload = "{\"ivme\":" + String(ivme, 2) + 
                     ",\"duman\":" + String(duman) + 
                     ",\"sos\":" + String(sos) + 
                     ",\"lat\":" + String(lat, 4) + 
                     ",\"lon\":" + String(lon, 4) + "}";
                     
    int httpResponseCode = http.PUT(payload);
    
    Serial.print("Firebase HTTP Kod: ");
    Serial.println(httpResponseCode);
    
    http.end();
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) return;

  // 1. SOS Butonu Kontrolü
  bool currentButtonState = digitalRead(sosButtonPin);
  if (lastButtonState == HIGH && currentButtonState == LOW) {
    sosToggleState = !sosToggleState; 
    delay(50); 
  }
  lastButtonState = currentButtonState;
  sosDurumuVal = sosToggleState ? 1 : 0;

  lcd.setCursor(0, 1);
  if (sosToggleState) {
    lcd.print("SOS: AKTIF      ");
  } else {
    lcd.print("SOS: YOK        ");
  }

  // 2. Duman / Buhar Sensörü Simülasyonu
  dumanDegeri = 180 + (millis() / 400) % 120; 

  // 3. İvme Simülasyonu
  ivmeX = 1.0 + (random(-20, 30) / 10.0);

  // 4. Sesli Uyarı Kontrolü ("Did did did" alarm mantığı)
  // Kaza durumu (ivme > 3.5) veya SOS aktifse (sosDurumuVal == 1) buzzer öter
  if (sosDurumuVal == 1 || ivmeX > 3.5 || dumanDegeri > 250) {
    digitalWrite(buzzerPin, HIGH);
    delay(100);
    digitalWrite(buzzerPin, LOW);
    delay(100);
    digitalWrite(buzzerPin, HIGH);
    delay(100);
    digitalWrite(buzzerPin, LOW);
  } else {
    digitalWrite(buzzerPin, LOW);
  }

  // 5. Google Cloud'a Gönderim (Her 3 saniyede bir)
  unsigned long simdikiZaman = millis();
  if (simdikiZaman - sonGonderimZamani >= gonderimAraligi) {
    sonGonderimZamani = simdikiZaman;

    firebaseVeriyiGonder(ivmeX, dumanDegeri, sosDurumuVal, latVal, lonVal);

    lcd.setCursor(0, 0);
    lcd.print("Veri Gonderildi  ");
  }
  
  delay(50); 
}
