try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time


class HTU21D:
    def __init__(self, i2c, addr=0x40):
        self.i2c = i2c
        self.addr = addr
        self.temperatura = 0.0
        self.humedad = 0.0

    def reiniciar(self):
        """Inicializa el sensor para una nueva medición."""
        self.i2c.writeto(self.addr, bytes([0xF3]))
        time.sleep_ms(50)
        d = self.i2c.readfrom(self.addr, 2)
        return (d[0] << 8) | d[1]

    def _read2(self, cmd, delay_ms=50):
        self.i2c.writeto(self.addr, bytes([cmd]))
        time.sleep_ms(delay_ms)
        data = self.i2c.readfrom(self.addr, 2)
        if len(data) < 2:
            raise OSError("HTU21D sin datos")
        return (data[0] << 8) | data[1]

    def temperature(self):
        raw = self._read2(0xF3, delay_ms=50)
        return -46.85 + (175.72 * raw / 65536.0)

    def humidity(self):
        raw = self._read2(0xF5, delay_ms=50)
        rh = -6.0 + (125.0 * raw / 65536.0)
        if rh < 0:
            rh = 0
        if rh > 100:
            rh = 100
        return rh

    def actualizar(self):
        try:
            self.temperatura = self.temperature()
            self.humedad = self.humidity()
            return True
        except Exception:
            return False

    def measure(self):
        return self.temperature(), self.humidity()

    async def _read2_async(self, cmd, delay_ms=50):
        self.i2c.writeto(self.addr, bytes([cmd]))
        await asyncio.sleep_ms(delay_ms)
        data = self.i2c.readfrom(self.addr, 2)
        return (data[0] << 8) | data[1]

    async def leer(self):
        """Devuelve (temperatura, humedad). Si el sensor falla: (None, None)."""
        try:
            raw_t = await self._read2_async(0xF3)
            raw_h = await self._read2_async(0xF5)
        except OSError:
            return None, None
        t = -46.85 + (175.72 * raw_t / 65536.0)
        rh = -6.0 + (125.0 * raw_h / 65536.0)
        return t, max(0, min(100, rh))
