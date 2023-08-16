#include <wiringPi.h>
#include <softPwm.h>
#include <stdio.h>

#define BUTTON_PIN 2  
#define SERVO_PIN 0   

int buttonState = LOW;
int prevButtonState = LOW;
int angle = 0;

void buttonCallback() {
    buttonState = digitalRead(BUTTON_PIN);

    if (buttonState != prevButtonState) {
        if (buttonState == HIGH) {
            angle += 90;  
            if (angle > 180) {
                angle = 0;  
            }
            printf("angle: %d\n", angle);
        }
    }

    prevButtonState = buttonState;
}

void setAngle(int angle) {
    int duty = (int)(((float)angle / 180.0) * 23.0 + 2.5);
    softPwmWrite(SERVO_PIN, duty);
}

int main() {
    if (wiringPiSetup() == -1) {
        printf("wiringPiSetup() failed\n");
        return 1;
    }

    pinMode(BUTTON_PIN, INPUT);
    pullUpDnControl(BUTTON_PIN, PUD_UP);
    wiringPiISR(BUTTON_PIN, INT_EDGE_FALLING, &buttonCallback);

    softPwmCreate(SERVO_PIN, 0, 200);

    while (1) {
        setAngle(angle);
        delay(10);
    }

    return 0;
}


