import RPi.GPIO as GPIO
import time
import Adafruit_DHT  # Import the DHT library
import firebase_admin
from firebase_admin import credentials, db

IN11 = 19  
IN22 = 26  

# DHT11 Sensor Pin
DHT_PIN = 17  # GPIO pin for DHT11 sensor

# Humidity Thresholds for control
HUMIDITY_HIGH_THRESHOLD = 140  # If humidity goes above this, turn off the humidifier
HUMIDITY_LOW_THRESHOLD = 80   # If humidity goes below this, turn on the humidifier

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

def loop():
    while True:
        hum_mode = "moderate"  # Default hum mode
        hum_auto = False  # Default hum auto mode
        turn_on_hum = False  # Default turn on hum mode
        is_hum_turned_on = True # Default "is hum turned on"
        
        humidity, temperature = read_dht11()  # Read humidity, temperature from DHT11 sensor
        print("Humidity:", humidity)
        print("Temperature: ",temperature)
        
        ref.update({
            'humidity':str(humidity),
            'temperature':str(temperature)
        })
        
        # Update the "is_hum_turned_on" based on Firebase value
        new_is_hum_turned_on = ref.child('isHumTurnedOn').get()
        if isinstance(new_is_hum_turned_on, bool):
            is_hum_turned_on = new_is_hum_turned_on
        #print("is_hum_turned_on:",is_hum_turned_on)
        
        # Update the hum auto mode based on Firebase value
        new_hum_auto = ref.child('humAuto').get()
        if isinstance(new_hum_auto, bool):
            hum_auto = new_hum_auto
        #print("hum_auto:",hum_auto)

        # Update the turn on hum mode based on Firebase value
        new_turn_on_hum = ref.child('turnOnHum').get()
        if isinstance(new_turn_on_hum, bool):
            turn_on_hum = new_turn_on_hum
        #print("turn_on_hum: ",turn_on_hum)
        
        if is_hum_turned_on:
            if hum_auto:
                # Check PM values and control pan motor accordingly
                if humidity > HUMIDITY_HIGH_THRESHOLD:
                    pumpOff()
                    print("hum auto stopped")
                elif humidity < HUMIDITY_LOW_THRESHOLD:
                    pumpOn()
                    print("hum auto started")
                    
            elif turn_on_hum:
                # Update the hum mode based on Firebase value
                new_hum_mode = ref.child('humMode').get()
                if new_hum_mode in ["sleeping", "weak", "moderate", "strong", "turbo"]:
                    hum_mode = new_hum_mode

                # Get GSG speed based on hum mode
                DELAY = set_GSG_speed(hum_mode)
                print("hum_mode: ",hum_mode)
                print("DELAY: ",DELAY)
                
                # Set GSG speed by updating the DELAY value
                pumpOn()
                time.sleep(10)
                pumpOff()
                time.sleep(DELAY)  # Repeat this pattern to control GSG speed

            # Set GSG speed by updating the DELAY value
            time.sleep(0.5)
        else:
            pass

        time.sleep(2)  # Delay before reading humidity again

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()

