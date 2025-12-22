#include <Wire.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include <PZEM004Tv30.h>
#include <LiquidCrystal_I2C.h>
#include <HTTPClient.h>

// ================= PIN DEFINITIONS =================
#define PZEM_RX_PIN 16
#define PZEM_TX_PIN 17
#define wifiPin 23

// ================= WIFI CREDENTIALS ================
const char* ssid = "ssid";
const char* password = "password";

// ================= SERVER DETAILS ==================
const char* serverBase = "https://***************************";
const char* device_id  = "001";

// ================= OBJECTS =========================
PZEM004Tv30 pzem(Serial2, PZEM_RX_PIN, PZEM_TX_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ================= TIMING ==========================
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 5000; // 5 seconds
int lcdPage = 0;

// ================= SETUP ===========================
void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, PZEM_RX_PIN, PZEM_TX_PIN);

  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Smart Meter");
  delay(2000);
  lcd.clear();
  pinMode(wifiPin, OUTPUT);
  digitalWrite(wifiPin, LOW);

  connectToWifi();
}

// ================= LOOP ============================
void loop() {
  float voltage = pzem.voltage();
  float current = pzem.current();
  float power   = pzem.power();
  float energy  = pzem.energy();

  // Check if PZEM is connected and reading properly
  if (isnan(voltage) && isnan(current) && isnan(power)) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("PZEM Not");
    lcd.setCursor(0, 1);
    lcd.print("Connected");
    Serial.println("PZEM-004T not responding!");
    delay(2000);
  } else {
    scrollLCD(voltage, current, power, energy);
  }

  if (millis() - lastSendTime >= sendInterval) {
    sendToServer(voltage, current, power, energy);
    lastSendTime = millis();
  }

  delay(1000);
}

// ================= WIFI CONNECTION =================
void connectToWifi() {
  lcd.print("WiFi Connecting");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  lcd.clear();
  lcd.print("WiFi Connected");
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  delay(1500);
  lcd.clear();
  digitalWrite(wifiPin, HIGH);
}

// ================= LCD SCROLL ======================
void scrollLCD(float v, float i, float p, float e) {
  lcd.clear();

  switch (lcdPage) {
    case 0:
      lcd.setCursor(0, 0);
      lcd.print("Voltage:");
      lcd.setCursor(0, 1);
      lcd.print(v);
      lcd.print(" V");
      break;

    case 1:
      lcd.setCursor(0, 0);
      lcd.print("Current:");
      lcd.setCursor(0, 1);
      lcd.print(i, 3);
      lcd.print(" A");
      break;

    case 2:
      lcd.setCursor(0, 0);
      lcd.print("Power:");
      lcd.setCursor(0, 1);
      lcd.print(p, 3);
      lcd.print(" W");
      break;

    case 3:
      lcd.setCursor(0, 0);
      lcd.print("Energy:");
      lcd.setCursor(0, 1);
      lcd.print(e, 3);
      lcd.print(" KWh");
      break;
  }

  lcdPage = (lcdPage + 1) % 4;
}

// ================= SEND DATA TO FASTAPI ============
void sendToServer(float v, float i, float p, float e) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Skipping send.");
    return;
  }
  
  // Properly check and handle NaN values
  if (isnan(v)) v = 0.00;
  if (isnan(i)) i = 0.00;
  if (isnan(p)) p = 0.00;
  if (isnan(e)) e = 0.000;

  HTTPClient http;

  String serverURL = String(serverBase) + device_id;

  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  StaticJsonDocument<256> doc;
  doc["voltage"] = v;
  doc["current"] = i;
  doc["power"]   = p;
  doc["energy"]  = e;

  String payload;
  serializeJson(doc, payload);

  // Print the actual JSON being sent
  Serial.println("\n========== SENDING DATA ==========");
  Serial.println("POST URL: " + serverURL);
  Serial.println("JSON Payload: " + payload);

  int httpResponseCode = http.POST(payload);

  Serial.print("HTTP Response Code: ");
  Serial.println(httpResponseCode);
  
  // Print server response 
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Server Response: " + response);
  } else {
    Serial.print("Error on HTTP request: ");
    Serial.println(httpResponseCode);
  }
  
  Serial.println("==================================\n");

  http.end();
}
