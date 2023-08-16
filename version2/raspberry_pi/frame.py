import firebase_admin
from firebase_admin import credentials, db
import pygame
import time
import requests
import sys

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

