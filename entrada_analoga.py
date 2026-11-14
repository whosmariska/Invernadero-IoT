from machine import Pin, ADC
import time

class SenalAnaloga:
    def __init__(self, pin_adc, atenuacion=ADC.ATTN_11DB, ancho=ADC.WIDTH_12BIT, vref=3.3):
        self.pin_adc = pin_adc
        self.vref = vref

        # configurar el ADC
        self.adc=ADC(Pin(self.pin_adc))
        self.adc.atten(atenuacion)
        self.adc.width(ancho) #resolucion de 12 bits (0-4095)

    def leer_valor(self):
        return self.adc.read()

    def leer_voltaje(self):
        valor_adc=self.leer_valor()
        voltaje=round((valor_adc/4095)*self.vref,2)
        return valor_adc, voltaje