import RPi.GPIO as GPIO
import time
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase
cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
})

# Reference to the Firebase database
ref = db.reference('lightData')

# Set GPIO mode and pins
GPIO.setmode(GPIO.BCM)
led_pin = 22  # GPIO pin for the LED
button_led_pin = 4  # GPIO pin for the LED button (pull-down)
servo_pin = 12  # GPIO pin for the servo motor (PWM)
button_servo_pin = 27  # GPIO pin for the servo button (pull-down)

# Initialize GPIO pins
GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(button_led_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(servo_pin, GPIO.OUT)
GPIO.setup(button_servo_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Set up PWM for the servo motor
pwm_servo = GPIO.PWM(servo_pin, 50)  # 50 Hz (standard for servos)
pwm_servo.start(0)  # Start with 0% duty cycle

# Variables to keep track of button states and LED state
led_button_pressed = False
led_state = False  # To keep track of LED state

def toggle_led():
    global led_state
    led_state = not led_state
    GPIO.output(led_pin, led_state)

def rotate_servo_90_degrees():
    pwm_servo.ChangeDutyCycle(7.5)  # 90 degrees (center position)
    time.sleep(1)  # Wait for the servo to reach the position
    pwm_servo.ChangeDutyCycle(0)  # Stop PWM signal

def update_servo_angle(angle):
    if angle == 1:
        rotate_servo_90_degrees()
    elif angle == 2:
        rotate_servo_90_degrees()
    elif angle == 3:
        rotate_servo_90_degrees()
    elif angle == 4:
        rotate_servo_90_degrees()

# Main loop
if __name__ == "__main__":
    try:
        while True:
            led_button_state = GPIO.input(button_led_pin)
            if led_button_state == GPIO.HIGH and not led_button_pressed:
                led_button_pressed = True
                toggle_led()
            elif led_button_state == GPIO.LOW and led_button_pressed:
                led_button_pressed = False

            current_turn_on_light = ref.child('turnOnLight').get()
            if current_turn_on_light:
                GPIO.output(led_pin, GPIO.HIGH)
            else:
                GPIO.output(led_pin, GPIO.LOW)

            servo_button_state = GPIO.input(button_servo_pin)
            if led_state and servo_button_state == GPIO.HIGH:
                rotate_servo_90_degrees()

            current_light_option = ref.child('lightOption').get()
            update_servo_angle(current_light_option)

    except KeyboardInterrupt:
        # Cleanup GPIO settings
        pwm_servo.stop()
        GPIO.cleanup()
