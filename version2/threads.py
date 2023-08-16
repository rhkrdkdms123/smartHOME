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
import def_function

def light_thread():
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

            time.sleep(0.1)  # Add a small delay to avoid excessive CPU usage

    except KeyboardInterrupt:
        # Cleanup GPIO settings
        pwm_servo.stop()
        GPIO.cleanup()


def frame_thread():
    # Initialize Firebase
    cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
    })

    # Reference to the Firebase database
    ref = db.reference('frameData')

    pygame.init()
    pygame.display.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)

    current_image = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  
                    pygame.quit()
                    sys.exit()

        turn_off_frame = ref.child('turnOffFrame').get()

        if turn_off_frame:
            pygame.display.quit() 
            while turn_off_frame:
                turn_off_frame = ref.child('turnOffFrame').get()
                time.sleep(1)
            
            pygame.display.init()
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)

        image_url = ref.child('imageUrl').get()

        if image_url and image_url != current_image:
            try:
                response = requests.get(image_url)
                image_data = response.content

                with open('current_image.jpg', 'wb') as f:
                    f.write(image_data)

                img = pygame.image.load('current_image.jpg')

                # Get the screen dimensions
                screen_width, screen_height = pygame.display.get_surface().get_size()

                # Resize the image to fit the screen
                img = pygame.transform.scale(img, (screen_width, screen_height))

                # Center the image on the screen
                img_rect = img.get_rect(center=(screen_width/2, screen_height/2))

                screen.fill((0, 0, 0))
                screen.blit(img, img_rect)
                pygame.display.flip()  

                current_image = image_url
            except Exception as e:
                print("Error:", e)

        time.sleep(1)

def air_thread():
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

            # Update the air auto mode based on Firebase value
            new_is_air_turned_on = ref.child('isAirTurnedOn').get()
            if isinstance(new_is_air_turned_on, bool):
                is_air_turned_on = new_is_air_turned_on
            #print("is_air_turned_on:",is_air_turned_on)
            
            # Update the air auto mode based on Firebase value
            new_air_auto = ref.child('airAuto').get()
            if isinstance(new_air_auto, bool):
                air_auto = new_air_auto
            #print("air_auto:",air_auto)

            # Update the turn on air mode based on Firebase value
            new_turn_on_air = ref.child('turnOnAir').get()
            if isinstance(new_turn_on_air, bool):
                turn_on_air = new_turn_on_air
            #print("turn_on_air: ",turn_on_air)
            
            if is_air_turned_on:
                if air_auto:
                    # Check PM values and control pan motor accordingly
                    if pm0_1 > 120 or pm2_5 > 120 or pm10 > 120:
                        print("Pan motor running")
                        setPanAngle(180)  # Adjust the angle as desired
                        pan_motor_running = True
                    else:
                        print("Pan motor stopped")
                        # Add code here to stop the pan motor
                        pan_motor_running = False
                elif turn_on_air:
                    # Update the air mode based on Firebase value
                    new_air_mode = ref.child('windPower').get()
                    if new_air_mode in ["sleeping", "weak", "moderate", "strong", "turbo"]:
                        air_mode = new_air_mode

                    # Get motor speed based on air mode
                    DELAY = set_motor_speed(air_mode)
                    print("air_mode: ",air_mode)
                    print("DELAY: ",DELAY)
                    
                    # Set motor speed by updating the DELAY value
                    setPanAngle(180)
                    time.sleep(DELAY)
                    GPIO.output(STEP_PIN, GPIO.LOW)
                    time.sleep(DELAY)  # Repeat this pattern to control motor speed

                # Set motor speed by updating the DELAY value
                time.sleep(0.5)
            else:
                pass

    except KeyboardInterrupt:
        pass

def humidity_control_thread():
    IN11 = 19  
    IN22 = 26  

    # DHT11 Sensor Pin
    DHT_PIN = 17  # GPIO pin for DHT11 sensor

    HUMIDITY_HIGH_THRESHOLD = 140
    HUMIDITY_LOW_THRESHOLD = 80

    # Initialize Firebase
    cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
    })

    # Reference to the Firebase database
    ref = db.reference('humData')

    try:
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

    except KeyboardInterrupt:
        pass

def window_control_thread():
    rainPin = 13
    servoPin = 16

    # SPI Configuration
    SPI_PORT = 0
    SPI_DEVICE = 0
    rain_adc_channel = 0

    # Initialize Firebase
    cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
    })

    # Reference to the Firebase database
    ref = db.reference('windowData')

    try:
        spi_instance = setup_spi()
        setup_rain()
        control_window(spi_instance)
    except KeyboardInterrupt:
        cleanup(spi_instance)
        destroy()


def music_control_thread():
    # Initialize Firebase
    cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
    })

    # Reference to the Firebase database
    ref = db.reference('speakerData')

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

    pygame.mixer.music.stop()