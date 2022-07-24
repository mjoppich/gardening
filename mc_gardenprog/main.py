from machine import Pin, I2C, ADC
import machine
import bme280
from csms import CSMS
import time
import urequests
import json


def collectSendData(temp, hum, pres, moisture, watering=False, post_data=True):
    global led

    if led.value() == 1:
        gpio_state = "ON"
    else:
        gpio_state = "OFF"

    sendData = {}
    sendData["gpio_state"] = gpio_state
    sendData["temp"] = temp
    sendData["humidity"] = hum
    sendData["airpressure"] = pres
    sendData["soilmoisture"] = moisture

    if watering:
        sendData["watering"] = 1

    if post_data:

        try:
            connectWIFI()

            headers = {'Content-Type': 'application/json'}
            response = urequests.post("http://garden.compbio.cc/send", json=sendData, headers=headers)
        except:
            machine.reset()

    return sendData


pump_off()

# ESP8266 - Pin assignment
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=10000)

adc = ADC(0)
csms = CSMS(adc, 600, 240)

initialStart = time.gmtime()
lastTimer = time.gmtime()
pumpEndTime = 0
waterMin = 0

response = urequests.get("http://garden.compbio.cc/sleepMin")
sleepMin = int(response.text)

response = urequests.get("http://garden.compbio.cc/waterMin")
waterMin = int(response.text)

response = urequests.get("http://garden.compbio.cc/start_watering")
startWatering = int(response.text)


def deep_sleep(secs):
    # configure RTC.ALARM0 to be able to wake the device
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    # set RTC.ALARM0 to fire after Xmilliseconds, waking the device
    rtc.alarm(rtc.ALARM0, secs * 1000)
    # put the device to sleep
    machine.deepsleep()



bme = bme280.BME280(i2c=i2c)
temp = bme.temperature
hum = bme.humidity
pres = bme.pressure
csms_raw = csms.read(10)

led.value(0)

sendData = collectSendData(temp, hum, pres, csms_raw)
#led off
led.value(1)

sleepTime = sleepMin * 60

if not startWatering:
    deep_sleep(sleepTime)

else:
    led.value(0)
    pump_on()

    collectSendData(temp, hum, pres, csms_raw, watering=True)

    while pumpMode == True:
        time.sleep(30)
        pumpMode = wateringTime(pumpEndTime)
        collectSendData(temp, hum, pres, csms_raw)

    pump_off()
    led.value(1)

    deep_sleep(sleepTime)
