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
import def_threads

if __name__ == "__main__":
    window_thread = threading.Thread(target=window_control_thread)
    window_thread.start()