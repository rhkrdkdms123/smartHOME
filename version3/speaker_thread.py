import firebase_admin
from firebase_admin import credentials, db
import pygame
import time
import threading

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

def music_thread():
    global current_music
    global is_playing

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