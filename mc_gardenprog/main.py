from machine import Pin, I2C, ADC
import machine
import bme280
from csms import CSMS
import time
import urequests
import json

def dateToSeconds(indate):
    x = (indate[3], indate[4], indate[5])
    x = x[0] * 60 * 60 + x[1] * 60 + x[2]
    return x

def dateToDateStr(indate):
    year, month, mday = (indate[0], indate[1], indate[2])
    return "{}/{}/{}".format(year, month, mday)

def tupleToSeconds(intuple):
    if len(intuple) > 2:
        secs = intuple[2]
    else:
        secs = 0
    return intuple[0] * 60 * 60 + intuple[1] * 60 + secs

def hmsToSeconds(intuple):
    return tupleToSeconds([int(x) for x in intuple.split(":")])

def seconds2hms(seconds, timeZone=0):
    sign = -1 if seconds < 0 else 1
    seconds = abs(seconds)

    minutes = seconds // 60
    hours = minutes // 60

    if (sign*hours)+timeZone >= 0:
        hours = ((sign*hours)+timeZone) % 24
    else:
        hours = (sign*hours)+timeZone

    return "{:>02}:{:>02}:{:>02}".format(hours, minutes % 60, seconds % 60)


def timingFunction():

    global lastTimer
    global initialStart
    global pumpEndTime

    currentTimer = time.gmtime()
    currentTimerSeconds = dateToSeconds(currentTimer)
    lastTimerSeconds = dateToSeconds(lastTimer)

    lastTimer = currentTimer
    waterTime = 15 * 60

    for alarmSecond in alarmSeconds:

        if alarmSecond <= currentTimerSeconds <= alarmSecond+waterTime:
            pumpEndTime = currentTimerSeconds + waterTime
            return True

    return False

def wateringTime( pumpEndTime ):

    currentTimer = time.gmtime()
    currentTimerSeconds = dateToSeconds(currentTimer)

    if currentTimerSeconds <= pumpEndTime:
        return True

    return False

def collectSendData(temp, hum, pres, timestamp, moisture):
    global lastTimer
    global initialStart
    global nextPumping
    global nextPumpingOut
    global alarmSeconds
    global timeZone
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
    sendData["timezone"] = timeZone

    sendData["last_timer"] = seconds2hms(dateToSeconds(lastTimer), timeZone)
    sendData["initial_start"] = dateToDateStr(initialStart) + " " + seconds2hms(dateToSeconds(initialStart))
    #sendData["alarm_times_utc"] = tuple([seconds2hms(x) for x in alarmSeconds])
    #sendData["alarm_times_local"] = tuple([seconds2hms(x, timeZone) for x in alarmSeconds])

    sendData["current_time_utc"] = seconds2hms(dateToSeconds(time.gmtime()))
    sendData["current_time_local"] = seconds2hms(dateToSeconds(time.gmtime()), timeZone)
    sendData["time_to_alarm"] = tuple([seconds2hms(x - dateToSeconds(time.gmtime()), 0) for x in alarmSeconds])
    sendData["times_to_alarm"] = tuple([x - dateToSeconds(time.gmtime()) for x in alarmSeconds])

    return sendData


pump_off()

# ESP8266 - Pin assignment
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=10000)

adc = ADC(0)
csms = CSMS(adc, 600, 240)

initialStart = time.gmtime()
lastTimer = time.gmtime()
pumpEndTime = 0

response = urequests.get("http://garden.compbio.cc/water_times")
alarm = json.loads(response.text)

response = urequests.get("http://garden.compbio.cc/timezone")
timeZone = int(response.text)


#alarm = [[7, 0], [19, 0]]
alarmSeconds = [tupleToSeconds(x) for x in alarm]

def deep_sleep(secs):
    # configure RTC.ALARM0 to be able to wake the device
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    # set RTC.ALARM0 to fire after Xmilliseconds, waking the device
    rtc.alarm(rtc.ALARM0, secs * 1000)
    # put the device to sleep
    machine.deepsleep()


led.value(0)
dateTuple = time.gmtime()

bme = bme280.BME280(i2c=i2c)
temp = bme.temperature
hum = bme.humidity
pres = bme.pressure
csms_raw = csms.read(10)

pumpMode = timingFunction()
sendData = collectSendData(temp, hum, pres, str(dateTuple), csms_raw)

headers = {'Content-Type': 'application/json'}
response = urequests.post("http://garden.compbio.cc/send", json=sendData, headers=headers)
led.value(1)

sleepMin = 15
sleepTime = sleepMin * 60

if not pumpMode:
    deep_sleep(sleepTime)

else:
    led.value(0)
    pump_on()

    while pumpMode == True:
        time.sleep(30)
        pumpMode = wateringTime(pumpEndTime)
        sendData = collectSendData(temp, hum, pres, str(dateTuple), csms_raw)

    pump_off()
    led.value(1)
    deep_sleep(sleepTime)
