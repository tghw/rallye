#include "Arduino.h"
#include "HardwareSerial.h"

const int clkPinA = 2;
const int dirPinA = 3;
volatile unsigned long encoderACount = 0;
volatile unsigned long encoderBCount = 0;
volatile unsigned long lastA = 0;
volatile unsigned long lastB = 0;

volatile unsigned long lastTime = 0;
volatile unsigned long now = 0;
volatile boolean changeFlag = false;

void encoderIntA() {
  if (digitalRead(dirPinA) == HIGH)
    encoderACount++;
  else
    encoderBCount++;
  changeFlag = true;
}

void setup() {
  Serial.begin(9600);
  pinMode(clkPinA, INPUT);  
  pinMode(dirPinA, INPUT);  
  attachInterrupt(0, encoderIntA, RISING);
}

void loop() {
 if (changeFlag) {
    changeFlag = false;
    
    /*
    Serial.print(encoderACount);
    Serial.print(' ');
    Serial.print(encoderBCount);
    Serial.print(' ');
    Serial.print(millis());
    Serial.print('\n');
    */   

    now = millis();
    if ((now - lastTime) > 1000) {
      Serial.print("Speed ");
      Serial.print(((encoderACount - lastA) * 1000 / 6) / (now - lastTime));
      Serial.print(' ');
      Serial.print(((encoderBCount - lastB) * 1000 / 6) / (now - lastTime));
      Serial.print('\n');
      lastA = encoderACount;
      lastB = encoderBCount;
      lastTime = now;
    }
  }
}

