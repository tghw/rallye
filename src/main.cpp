#include "Arduino.h"
#include "HardwareSerial.h"

const int clkPinA = 2;
const int dirPinA = 3;
volatile unsigned long encoderACount = 0;
volatile unsigned long encoderBCount = 0;
volatile unsigned long tempA = 0;
volatile unsigned long tempB = 0;

volatile unsigned long lastTime = 0;
volatile unsigned long now = 0;

void encoderIntA() {
    if (digitalRead(dirPinA) == HIGH) {
        encoderACount++;
    }
    else {
        encoderBCount++;
    }
}

void setup() {
    Serial.begin(9600);
    pinMode(clkPinA, INPUT);  
    pinMode(dirPinA, INPUT);  
    attachInterrupt(0, encoderIntA, RISING);
}

void loop() {
    now = millis();
    if ((now - lastTime) >= 1000) {
        lastTime = now;
        tempA = encoderACount;
        encoderACount = 0;
        tempB = encoderBCount;
        encoderBCount = 0;
        Serial.print(tempA);
        Serial.print('|');
        Serial.print(tempB);
        Serial.print('\n');
    }
}

