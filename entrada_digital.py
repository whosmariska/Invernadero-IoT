from machine import Pin
import time

class EntradaDigital:
    def __init__(self, pin, pull=Pin.PULL_DOWN):
        self._pin = Pin(pin, Pin.IN, pull)
 
    def leer(self):
        return self._pin.value()