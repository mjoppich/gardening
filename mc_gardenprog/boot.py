
try:
  import usocket as socket
except:
  import socket

from machine import Pin, reset
import network
import time
import esp
esp.osdebug(None)

import gc
gc.collect()

led = Pin(2, Pin.OUT, Pin.PULL_UP)
led.value(0)

pump = Pin(14, Pin.OUT, Pin.PULL_UP)
pump.value(0)

def pump_on():
    led.value(1)
    pump.value(1)

def pump_off():
    led.value(0)
    pump.value(0)

pump_off()

led.value(1)

def connectWIFI():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():

        sta_if.active(True)
        sta_if.connect('xxx', 'xxx')
        while not sta_if.isconnected():
            pass

try:
    connectWIFI()
except:
    reset()

led.value(0)
pump_off()
