import RPi.GPIO as GPIO
import time
import spidev
import firebase_admin
from firebase_admin import credentials, db
import threading

# Initialize Firebase
cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
})

# Reference to the Firebase database
ref = db.reference('windowData')

rainPin = 13
servoPin = 16

SPI_PORT = 0
SPI_DEVICE = 0
rain_adc_channel = 0

def setup_spi():
    spi = spidev.SpiDev()
    spi.open(SPI_PORT, SPI_DEVICE)
    spi.max_speed_hz = 1000000  # Set SPI speed to 1 MHz
    return spi

def read_adc(channel, spi):
    adc_value = spi.xfer2([1, (8 + channel) << 4, 0])
    digital_value = ((adc_value[1] & 3) << 8) + adc_value[2]
    return digital_value

def setup():
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

def loop(spi):
    try:
        while True:
            living_room_auto = ref.child('LivingRoomWindowAuto').get()
            close_living_room_window = ref.child('closeLivingRoomWindow').get()
            rain_value = read_adc(rain_adc_channel, spi)

            if living_room_auto:
                living_room_rain_value = None
                is_living_room_window_closed = None

                if rain_value > 1000:
                    print("No rain detected.")
                    setAngle(90)
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
                    print("close_living_room_window: ", close_living_room_window)
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(spi)
        destroy()

def cleanup(spi):
    spi.close()
    servo.stop()
    GPIO.cleanup()

def destroy():
    pass  # You can add any cleanup code here if needed