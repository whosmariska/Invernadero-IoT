import time
import framebuf

class LcdI2C:
    """Driver HD44780 en modo 4 bits a través del PCF8574.
    Mapeo del módulo: P0=RS, P1=RW, P2=E, P3=luz de fondo, P4-P7=D4-D7."""
    RS, EN, LUZ = 0x01, 0x04, 0x08
 
    def __init__(self, i2c, addr, cols=16, rows=2):
        self.i2c, self.addr = i2c, addr
        self.cols, self.rows = cols, rows
        time.sleep_ms(50)
        for _ in range(3):                 # secuencia de arranque a 4 bits
            self._pulso(0x30)
            time.sleep_ms(5)
        self._pulso(0x20)
        self.comando(0x28)                 # 4 bits, 2 líneas, 5x8
        self.comando(0x0C)                 # display encendido, sin cursor
        self.comando(0x06)                 # cursor avanza a la derecha
        self.limpiar()
 
    def _pulso(self, dato):
        self.i2c.writeto(self.addr, bytes([dato | self.LUZ | self.EN]))
        time.sleep_us(2)
        self.i2c.writeto(self.addr, bytes([(dato | self.LUZ) & ~self.EN]))
        time.sleep_us(60)
 
    def _byte(self, valor, modo):
        self._pulso((valor & 0xF0) | modo)
        self._pulso(((valor << 4) & 0xF0) | modo)
 
    def comando(self, c):
        self._byte(c, 0)
 
    def limpiar(self):
        self.comando(0x01)
        time.sleep_ms(3)
 
    def linea(self, fila, texto):
        """Escribe una línea completa (rellena con espacios para no dejar basura)."""
        texto = (texto + " " * self.cols)[:self.cols]
        self.comando(0x80 | (0x40 * fila))
        for ch in texto:
            self._byte(ord(ch), self.RS)


LCDI2C = LcdI2C