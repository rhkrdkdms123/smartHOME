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
import spidev

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

def setPanAngle(angle):
    # Check angle limits
    angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))

    # Calculate the number of steps required
    total_steps = int(angle * 200 / 180)  # Assuming 200 steps per revolution

    # Set the motor direction
    if total_steps >= 0:
        GPIO.output(DIR_PIN, GPIO.LOW)  # Rotate clockwise
    else:
        GPIO.output(DIR_PIN, GPIO.HIGH)  # Rotate counter-clockwise

    # Get the start time
    start_time = time.time()

    # Perform the steps for 8 seconds
    while time.time() - start_time < 8:
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(DELAY)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(DELAY)

def read_pm2008_data():
    bus = smbus.SMBus(1)

    data = bus.read_i2c_block_data(PM2008_ADDRESS, 0x00, 32)

    status = int(data[2])
    measuring_mode = 256 * int(data[3]) + int(data[4])
    calib_coeff = 256 * int(data[5]) + int(data[6])
    pm0_1 = 256 * int(data[7]) + int(data[8])
    pm2_5 = 256 * int(data[9]) + int(data[10])
    pm10 = 256 * int(data[11]) + int(data[12])

    return status, measuring_mode, calib_coeff, pm0_1, pm2_5, pm10
    
def set_motor_speed(air_mode):
    # Set motor speed based on air mode and return DELAY
    if air_mode == "sleeping":
        return 0.01  # Set the desired delay value for sleeping mode
    elif air_mode == "weak":
        return 0.005  # Set the desired delay value for weak mode
    elif air_mode == "moderate":
        return 0.002  # Set the desired delay value for moderate mode
    elif air_mode == "strong":
        return 0.001  # Set the desired delay value for strong mode
    elif air_mode == "turbo":
        return 0.0005  # Set the desired delay value for terbo mode
    else:
        return 0.001  # Default delay value
    
def setup_hum():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IN11, GPIO.OUT)
    GPIO.setup(IN22, GPIO.OUT)

def pumpOn():
    GPIO.output(IN11, GPIO.HIGH)  # Set input 1 to high
    GPIO.output(IN22, GPIO.LOW)   # Set input 2 to low
    print("ON")

def pumpOff():
    GPIO.output(IN11, GPIO.LOW)  # Set input 1 to low
    GPIO.output(IN22, GPIO.LOW)  # Set input 2 to low
    print("OFF")

def read_dht11():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, DHT_PIN)
    return humidity, temperature
    
def set_GSG_speed(hum_mode):
    # Set GSG speed based on hum mode and return DELAY
    if hum_mode == "weak":
        return 1  # Set the desired delay value for weak mode
    elif hum_mode == "moderate":
        return 0.5  # Set the desired delay value for moderate mode
    elif hum_mode == "strong":
        return 0.1  # Set the desired delay value for strong mode
    else:
        return 0.1  # Default delay value
    
def setup_spi():
        spi = spidev.SpiDev()
        spi.open(SPI_PORT, SPI_DEVICE)
        spi.max_speed_hz = 1000000  # Set SPI speed to 1 MHz
        return spi

def read_adc(channel, spi):
    adc_value = spi.xfer2([1, (8 + channel) << 4, 0])
    digital_value = ((adc_value[1] & 3) << 8) + adc_value[2]
    return digital_value

def setup_rain():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(servoPin, GPIO.OUT)
    GPIO.output(servoPin, GPIO.LOW)
    GPIO.setup(rainPin, GPIO.IN)

    global servo
    servo = GPIO.PWM(servoPin, 50)  # 50 Hz (20 ms PWM period)
    servo.start(0)  # Starts PWM with duty cycle of 0 (servo at 0 degrees)

def setAngle(angle):
    dutyCycle = 2 + (angle / 18)  # Map angle (0-180) to duty cycle (2-12)
    servo.ChangeDutyCycle(dutyCycle)
    time.sleep(0.3)  # Allow servo time to move
    
def is_rain_detected():
    return GPIO.input(rainPin) == GPIO.LOW

def control_window(spi):
    try:
        while True:
            living_room_auto = ref.child('LivingRoomWindowAuto').get()
            close_living_room_window = ref.child('closeLivingRoomWindow').get()
            rain_value = read_adc(rain_adc_channel, spi)

            if living_room_auto:
                # 데이터 업데이트를 처리하기 전에 임시 변수에 데이터를 저장
                living_room_rain_value = None
                is_living_room_window_closed = None

                if rain_value > 1000:
                    print("No rain detected.")
                    setAngle(90)  # open the window
                    time.sleep(1)
                    living_room_rain_value = "No Rain"
                    is_living_room_window_closed = False

                elif rain_value > 500:
                    print("light rain")
                    setAngle(0)
                    time.sleep(1)
                    living_room_rain_value = "Weak Rain"
                    is_living_room_window_closed = True

                elif rain_value > -1:
                    print("rain detected")
                    setAngle(0)
                    time.sleep(1)
                    living_room_rain_value = "Heavy Rain"
                    is_living_room_window_closed = True

                ref.update({
                    'LivingRoomRainValue': living_room_rain_value,
                    'isLivingRoomWindowClosed': is_living_room_window_closed
                })
            else:
                if close_living_room_window:
                    setAngle(0)
                    time.sleep(1)
                    ref.update({
                        'isLivingRoomWindowClosed': True
                    })
                    print("Closed manually")
                elif not close_living_room_window:
                    setAngle(90)
                    time.sleep(1)
                    ref.update({
                        'isLivingRoomWindowClosed': False
                    })
                    print("Opened manually")
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(spi)
        destroy()

def cleanup(spi):
    spi.close()
    servo.stop()
    GPIO.cleanup()

def destroy():
    pass  