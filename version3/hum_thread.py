import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import firebase_admin
from firebase_admin import credentials, db
import threading

IN11 = 19
IN22 = 26

DHT_PIN = 17

HUMIDITY_HIGH_THRESHOLD = 140
HUMIDITY_LOW_THRESHOLD = 80

# Initialize Firebase
cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
})

# Reference to the Firebase database
ref = db.reference('humData')

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IN11, GPIO.OUT)
    GPIO.setup(IN22, GPIO.OUT)

def pumpOn():
    GPIO.output(IN11, GPIO.HIGH)
    GPIO.output(IN22, GPIO.LOW)
    print("ON")

def pumpOff():
    GPIO.output(IN11, GPIO.LOW)
    GPIO.output(IN22, GPIO.LOW)
    print("OFF")

def read_dht11():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, DHT_PIN)
    return humidity, temperature

def set_GSG_speed(hum_mode):
    if hum_mode == "weak":
        return 1
    elif hum_mode == "moderate":
        return 0.5
    elif hum_mode == "strong":
        return 0.1
    else:
        return 0.1

def humidity_control_thread():
    try:
        while True:
            hum_mode = "moderate"
            hum_auto = False
            turn_on_hum = False
            is_hum_turned_on = True

            humidity, temperature = read_dht11()
            print("Humidity:", humidity)
            print("Temperature:", temperature)

            ref.update({
                'humidity': str(humidity),
                'temperature': str(temperature)
            })

            new_is_hum_turned_on = ref.child('isHumTurnedOn').get()
            if isinstance(new_is_hum_turned_on, bool):
                is_hum_turned_on = new_is_hum_turned_on

            new_hum_auto = ref.child('humAuto').get()
            if isinstance(new_hum_auto, bool):
                hum_auto = new_hum_auto

            new_turn_on_hum = ref.child('turnOnHum').get()
            if isinstance(new_turn_on_hum, bool):
                turn_on_hum = new_turn_on_hum

            if is_hum_turned_on:
                if hum_auto:
                    if humidity > HUMIDITY_HIGH_THRESHOLD:
                        pumpOff()
                        print("hum auto stopped")
                    elif humidity < HUMIDITY_LOW_THRESHOLD:
                        pumpOn()
                        print("hum auto started")

                elif turn_on_hum:
                    new_hum_mode = ref.child('humMode').get()
                    if new_hum_mode in ["sleeping", "weak", "moderate", "strong", "turbo"]:
                        hum_mode = new_hum_mode

                    DELAY = set_GSG_speed(hum_mode)
                    print("hum_mode:", hum_mode)
                    print("DELAY:", DELAY)

                    pumpOn()
                    time.sleep(10)
                    pumpOff()
                    time.sleep(DELAY)

                time.sleep(0.5)
            else:
                pass

            time.sleep(2)

    except KeyboardInterrupt:
        pass

def destroy():
    GPIO.cleanup()