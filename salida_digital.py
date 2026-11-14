from machine import Pin
import time
from expansor import PinExp


def _crear_pin(expansor, pin):
    """Con expansor, 'pin' es la salida Q0..Q7 del 595 (0 a 7).
    Sin expansor (None), 'pin' es un GPIO normal de la ESP32."""
    if expansor is None:
        return Pin(pin, Pin.OUT)
    return PinExp(expansor, pin)


class SalidaDigital:

    def __init__(self, pin, activo_alto=True, expansor=None):
        self._pin = _crear_pin(expansor, pin)
        self._activo_alto = activo_alto
        self.estado = 0
        self.apagar()

    def encender(self):
        self._pin.value(1 if self._activo_alto else 0)
        self.estado = 1

    def apagar(self):
        self._pin.value(0 if self._activo_alto else 1)
        self.estado = 0

    def alternar(self):
        if self.estado:
            self.apagar()
        else:
            self.encender()


class Rele:
    # Con el transistor NPN delante de cada relé, la señal ya llega invertida:
    # 595 en alto -> relé encendido. Por eso activo_en_bajo va en False.
    def __init__(self, expansor, pin, activo_en_bajo=False):
        self.pin = _crear_pin(expansor, pin)
        self.activo_en_bajo = activo_en_bajo
        self.encendido = False
        self.apagar()

    def encender(self):
        self.pin.value(0 if self.activo_en_bajo else 1)
        self.encendido = True

    def apagar(self):
        self.pin.value(1 if self.activo_en_bajo else 0)
        self.encendido = False


class BombaRiego(Rele):
    def __init__(self, expansor, pin, riego_intervalo_ms=3000,
                 riego_duracion_ms=5000, suelo_seco=35, activo_en_bajo=False):
        super().__init__(expansor, pin, activo_en_bajo)   # crea self.pin y self.encendido
        self.t_inicio = 0
        self.t_fin = -riego_intervalo_ms
        self.riego_intervalo_ms = riego_intervalo_ms
        self.riego_duracion_ms = riego_duracion_ms
        self.suelo_seco = suelo_seco
        self.riegos = 0

    def actualizar(self, humedad_suelo):
        ahora = time.ticks_ms()
        if self.encendido:
            if time.ticks_diff(ahora, self.t_inicio) >= self.riego_duracion_ms:
                self.apagar()
                self.t_fin = ahora
        elif humedad_suelo < self.suelo_seco and \
                time.ticks_diff(ahora, self.t_fin) >= self.riego_intervalo_ms:
            self.encender()
            self.t_inicio = ahora
            self.riegos += 1


class Ventilador(Rele):
    def __init__(self, expansor, pin, t_on, t_off, activo_en_bajo=False):
        super().__init__(expansor, pin, activo_en_bajo)
        self.t_on, self.t_off = t_on, t_off
        self.eventos = 0

    def pide_encender(self, temp):
        if temp >= self.t_on:
            return True
        if temp < self.t_off:
            return False
        return self.encendido

    def fijar(self, estado):
        if estado and not self.encendido:
            self.eventos += 1
            self.encender()
        elif not estado and self.encendido:
            self.apagar()


class Indicadores:
    # LEDs: salida del 595 -> resistencia -> LED -> GND, así que 1 = encendido
    def __init__(self, expansor, sr_verde=3, sr_amarillo=4, sr_rojo=5, sr_azul=6, sr_blanco=7):
        self.verde = PinExp(expansor, sr_verde)
        self.amarillo = PinExp(expansor, sr_amarillo)
        self.rojo = PinExp(expansor, sr_rojo)
        self.azul = PinExp(expansor, sr_azul)
        self.blanco = PinExp(expansor, sr_blanco)

    def temperatura(self, vent_on, extr_temp_on):
        self.rojo.value(1 if extr_temp_on else 0)
        self.amarillo.value(1 if (vent_on and not extr_temp_on) else 0)
        self.verde.value(0 if vent_on else 1)

    def humedad(self, hr, hr_baja=40, hr_alta=65):
        self.azul.value(1 if hr < hr_baja else 0)
        self.blanco.value(1 if hr_baja <= hr < hr_alta else 0)