import RPi.GPIO as GPIO
import time
import smbus
import Adafruit_DHT
import pygame
import firebase_admin
from firebase_admin import credentials, db
import threading
import requests
import sys

# Initialize Firebase
cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
})

# Reference to the Firebase database
ref = db.reference()

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Set up pins
rainPin = 13
servoPin = 12  # GPIO pin for the servo motor (PWM)

DHT_PIN = 17  # GPIO pin for DHT11 sensor

led_pin = 22  # GPIO pin for the LED
button_led_pin = 4  # GPIO pin for the LED button (pull-down)
button_servo_pin = 27  # GPIO pin for the servo button (pull-down)

# Initialize hardware components
GPIO.setup(servoPin, GPIO.OUT)
GPIO.setup(rainPin, GPIO.IN)

GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(button_led_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(button_servo_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Shared variables
humidity_threshold = 140
# Define other shared variables here

# Initialize servo motor
pwm_servo = GPIO.PWM(servoPin, 50)  # 50 Hz (standard for servos)
pwm_servo.start(0)  # Start with 0% duty cycle

# Variables to keep track of button states and LED state
led_button_pressed = False
led_state = False  # To keep track of LED state

def read_adc(channel, spi):
    adc_value = spi.xfer2([1, (8 + channel) << 4, 0])
    digital_value = ((adc_value[1] & 3) << 8) + adc_value[2]
    return digital_value

def read_dht11():
    humidity, _ = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, DHT_PIN)
    return humidity

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

def control_humidifier_auto(humidity):
    global humidity_threshold
    if humidity > humidity_threshold:
        # Turn off humidifier
        ref.update({'isHumTurnedOn': False})
    else:
        # Turn on humidifier
        ref.update({'isHumTurnedOn': True})

def control_air_purifier():
    try:
        while True:
            air_mode = ref.child('windPower').get()
            if air_mode:
                ref.update({'isAirTurnedOn': True, 'airAuto': False, 'turnOnAir': True})
            else:
                ref.update({'isAirTurnedOn': False, 'airAuto': False, 'turnOnAir': False})
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def control_window():
    try:
        while True:
            rain_value = read_rain_sensor()
            if rain_value > 1000:
                ref.update({'LivingRoomWindowAuto': True})
            else:
                ref.update({'LivingRoomWindowAuto': False})
            time.sleep(1)
    except KeyboardInterrupt:
        pass

def read_rain_sensor():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    rain_value = read_adc(0, spi)
    spi.close()
    return rain_value

def play_background_music():
    pygame.init()
    pygame.mixer.init()

    mp3_file_paths = {
        1: "/home/pi/IoT/bgm/karma_ost.mp3",
        2: "/home/pi/IoT/bgm/Perfect_for_me.mp3",
        3: "/home/pi/IoT/bgm/See_the_World_Piano_Version.mp3",
        4: "/home/pi/IoT/bgm/rain_sound.mp3"
    }

    current_music = 0
    is_playing = False

    while True:
        turn_off_the_music = ref.child('turnOfftheMusic').get()

        if is_playing:
            new_current_music = ref.child('currentMusic').get()
            if new_current_music is not None and new_current_music != current_music:
                pygame.mixer.music.stop()
                current_music = new_current_music
                mp3_file_path = mp3_file_paths.get(current_music)
                if mp3_file_path:
                    pygame.mixer.music.load(mp3_file_path)
                    pygame.mixer.music.play()
        elif not turn_off_the_music:
            current_music = ref.child('currentMusic').get()
            if current_music is not None:
                mp3_file_path = mp3_file_paths.get(current_music)
                if mp3_file_path:
                    pygame.mixer.music.load(mp3_file_path)
                    pygame.mixer.music.play()
                    is_playing = True

        elif is_playing and turn_off_the_music:
            pygame.mixer.music.stop()
            is_playing = False

        time.sleep(1)

def setPanAngle(angle):
    dutyCycle = 2 + (angle / 18)  # Map angle (0-180) to duty cycle (2-12)
    pwm_servo.ChangeDutyCycle(dutyCycle)
    time.sleep(0.3)  # Allow servo time to move

def control_window_servo():
    try:
        while True:
            living_room_auto = ref.child('LivingRoomWindowAuto').get()
            close_living_room_window = ref.child('closeLivingRoomWindow').get()

            if living_room_auto:
                rain_value = read_adc(rain_adc_channel, spi)
                living_room_rain_value = None
                is_living_room_window_closed = None

                if rain_value > 1000:
                    print("No rain detected.")
                    setPanAngle(90)  # Open the window
                    time.sleep(1)
                    living_room_rain_value = "No Rain"
                    is_living_room_window_closed = False
                # Other conditions here

                ref.update({
                    'LivingRoomRainValue': living_room_rain_value,
                    'isLivingRoomWindowClosed': is_living_room_window_closed
                })
            else:
                if close_living_room_window:
                    setPanAngle(0)
                    time.sleep(1)
                    ref.update({'isLivingRoomWindowClosed': True})
                elif not close_living_room_window:
                    setPanAngle(90)
                    time.sleep(1)
                    ref.update({'isLivingRoomWindowClosed': False})

            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(spi)
        destroy()

# Set up SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000  # Set SPI speed to 1 MHz

# Create and start threads
air_thread = threading.Thread(target=control_air_purifier)
window_thread = threading.Thread(target=control_window)
music_thread = threading.Thread(target=play_background_music)
window_servo_thread = threading.Thread(target=control_window_servo)

air_thread.start()
window_thread.start()
music_thread.start()
window_servo_thread.start()

try:
    while True:
        humidity = read_dht11()
        auto_mode = ref.child('autoMode').get()
        if auto_mode:
            control_humidifier_auto(humidity)
        time.sleep(1)
except KeyboardInterrupt:
    pass

# Clean up
spi.close()
pwm_servo.stop()
GPIO.cleanup()
pygame.mixer.quit()
