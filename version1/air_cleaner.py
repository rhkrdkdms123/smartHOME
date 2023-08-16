import RPi.GPIO as GPIO
import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz=500000

dustLED=20

GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)
GPIO.setup(dustLED,GPIO.OUT)

def read_adc(adc_channel):
adcValue=0
buff = spi.xfer2([1, (8 + adc_channel) << 4, 0])
data = ((buff[1] & 3) << 8) + buff[2]
return data

def convert_to_ug_per_m3(sensor_value):
    voltage = sensor_value * (3.3 / 1023)  
    density = (0.17 * voltage - 0.1) * 1000  
    return density

while True:
GPIO.output(dustLED, GPIO.LOW)
time.sleep(0.00028)

dustAdcChannel=0
dustSensor_value = read_adc(dustAdcChannel)
time.sleep(0.00004)
   
GPIO.output(dustLED, GPIO.HIGH)
time.sleep(0.00968)
   
#density = convert_to_ug_per_m3(sensor_value)
#print("dust: {:.2f} ug/m3".format(density))
calVoltage=dustSensor_value*(5.0/1024.0)
dust_data=(0.172*calVoltage-0.01)*1000
print("dust %d"%dust_data)
time.sleep(1)  