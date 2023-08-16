import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import RPi_I2C_driver

GPIO.setmode(GPIO.BCM)
GPIO.setup(26,GPIO.OUT)

sensor = Adafruit_DHT.DHT11

pin = 4

mylcd=RPi_I2C_driver.lcd()
mylcd.lcd_clear()

try:
	while True :
		if h is not None and t is not None:
			h, t = Adafruit_DHT.read_retry(sensor, pin)
			print("Temperature = {0:0.1f}*C Humidity = {1:0.1f}%".format(t, h))
			mylcd.lcd_display_string("Humidity: "+str(h),1)
			if h>70.0:
				GPIO.output(26,True)
				#time.sleep(2)
			else :
				GPIO.output(26,False)
		else:
			print('Read error')
			time.sleep(100)	
		
except KeyboardInterrupt:
	print("Terminated by Keyboard")

finally:
	print("End of Program")
