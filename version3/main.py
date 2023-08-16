import threading
import time
import RPi.GPIO as GPIO
import firebase_admin
from firebase_admin import credentials

# Initialize Firebase
cred = credentials.Certificate("/home/pi/IoT/iothome-30e40-firebase-adminsdk-enn92-3a563acd66.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://iothome-30e40-default-rtdb.firebaseio.com/'
})

# Import thread modules
import air_thread
import frame_thread
import hum_thread
import light_thread
import speaker_thread
import window_thread

def main():
    try:
        # Create and start each thread
        threads = []

        # Add thread instances
        air_thread_instance = threading.Thread(target=air_thread.air_quality_thread)
        threads.append(air_thread_instance)

        frame_thread_instance = threading.Thread(target=frame_thread.display_thread)
        threads.append(frame_thread_instance)

        hum_thread_instance = threading.Thread(target=hum_thread.humidity_control_thread)
        threads.append(hum_thread_instance)

        light_thread_instance = threading.Thread(target=light_thread.light_control_thread)
        threads.append(light_thread_instance)

        spi_instance = window_thread.setup_spi()
        threads.append(threading.Thread(target=window_thread.loop, args=(spi_instance,)))

        # Start all threads
        for thread in threads:
            thread.start()

        # Main loop (if needed)
        while True:
            pass

    except KeyboardInterrupt:
        # Clean up each thread
        for thread in threads:
            if thread == speaker_thread_instance:
                pygame.mixer.music.stop()
                thread.join()
                pygame.quit()
            elif thread == hum_thread_instance:
                try:
                    thread.join()
                except KeyboardInterrupt:
                    hum_thread.destroy()
            elif thread == threading.Thread(target=window_thread.loop, args=(spi_instance,)):
                window_thread.cleanup(spi_instance)
            else:
                thread.join()

        GPIO.cleanup()  # Clean up GPIO settings

if __name__ == '__main__':
    main()
