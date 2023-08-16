import smbus
import time
import RPi.GPIO as GPIO
import firebase_admin
from firebase_admin import credentials, db
import threading

PM2008_ADDRESS = 0x28

# Initialize Firebase
cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
})

# Reference to the Firebase database
ref = db.reference('airData')

# Motor driver pins
DIR_PIN = 20
STEP_PIN = 21

# Step delay (controls motor speed)                    
DELAY = 0.001

MIN_ANGLE = 0
MAX_ANGLE = 180

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

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
    if air_mode == "sleeping":
        return 0.01
    elif air_mode == "weak":
        return 0.005
    elif air_mode == "moderate":
        return 0.002
    elif air_mode == "strong":
        return 0.001
    elif air_mode == "turbo":
        return 0.0005
    else:
        return 0.001
        
def air_quality_thread():
    try:
        pan_motor_running = False
        air_mode = "moderate"  # Default air mode
        air_auto = False  # Default air auto mode
        turn_on_air = False  # Default turn on air mode
        is_air_turned_on = True # Default "is air turned on"

        while True:
            status, measuring_mode, calib_coeff, pm0_1, pm2_5, pm10 = read_pm2008_data()
            ref.update({
                'PM0_1':str(pm0_1),
                'PM2_5':str(pm2_5),
                'PM10':str(pm10)
            })

            new_is_air_turned_on = ref.child('isAirTurnedOn').get()
            if isinstance(new_is_air_turned_on, bool):
                is_air_turned_on = new_is_air_turned_on
            
            new_air_auto = ref.child('airAuto').get()
            if isinstance(new_air_auto, bool):
                air_auto = new_air_auto

            new_turn_on_air = ref.child('turnOnAir').get()
            if isinstance(new_turn_on_air, bool):
                turn_on_air = new_turn_on_air

            if is_air_turned_on:
                if air_auto:
                    if pm0_1 > 120 or pm2_5 > 120 or pm10 > 120:
                        print("Pan motor running")
                        setPanAngle(180)  # Adjust the angle as desired
                        pan_motor_running = True
                    else:
                        print("Pan motor stopped")
                        # Add code here to stop the pan motor
                        pan_motor_running = False
                elif turn_on_air:
                    new_air_mode = ref.child('windPower').get()
                    if new_air_mode in ["sleeping", "weak", "moderate", "strong", "turbo"]:
                        air_mode = new_air_mode

                    DELAY = set_motor_speed(air_mode)
                    print("air_mode: ",air_mode)
                    print("DELAY: ",DELAY)
                    
                    setPanAngle(180)
                    time.sleep(DELAY)
                    GPIO.output(STEP_PIN, GPIO.LOW)
                    time.sleep(DELAY)  # Repeat this pattern to control motor speed

                time.sleep(0.5)
            else:
                pass
                
    except KeyboardInterrupt:
        pass