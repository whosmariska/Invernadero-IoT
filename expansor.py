from machine import Pin

class Registro595:
    """74HC595: 8 salidas extra con 3 cables (datos, reloj y latch).
    Las salidas entregan corriente (nivel 1 = 3.3 V), a diferencia de un PCF8574."""
 
    def __init__(self, pin_ds, pin_clk, pin_latch, inicial=0x00):
        self.ds = Pin(pin_ds, Pin.OUT, value=0)
        self.clk = Pin(pin_clk, Pin.OUT, value=0)
        self.latch = Pin(pin_latch, Pin.OUT, value=0)
        self.byte = inicial
        self._enviar()
 
    def _enviar(self):
        for i in range(7, -1, -1):          # primero el bit 7 (Q7)
            self.ds.value((self.byte >> i) & 1)
            self.clk.value(1)
            self.clk.value(0)
        self.latch.value(1)                 # copia el registro a las salidas
        self.latch.value(0)
 
    def poner(self, bit, nivel):
        nuevo = (self.byte | (1 << bit)) if nivel else (self.byte & ~(1 << bit))
        if nuevo != self.byte:              # solo envía si algo cambió
            self.byte = nuevo
            self._enviar()

class PinExp:
    """Imita a machine.Pin: value(1) = salida en alto, value(0) = en bajo."""
 
    def __init__(self, expansor, bit):
        self.exp, self.bit = expansor, bit
 
    def value(self, v):
        self.exp.poner(self.bit, bool(v))
 
 
def salida(pin):
    """Acepta un número de GPIO o un PinExp ya creado."""
    return Pin(pin, Pin.OUT) if isinstance(pin, int) else pin
 