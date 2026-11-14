from machine import Pin, ADC


def pct(valor, v0, v100):
    """Convierte lectura cruda a porcentaje 0-100 (v0 -> 0 %, v100 -> 100 %)."""
    p = (valor - v0) * 100 / (v100 - v0)
    return max(0, min(100, p))


class SensorLuz:
    def __init__(self, pin, ldr_oscuro_raw=4095, ldr_luz_raw=0):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.ldr_oscuro_raw = ldr_oscuro_raw
        self.ldr_luz_raw = ldr_luz_raw

    def leer(self, ldr_oscuro_raw=None, ldr_luz_raw=None):
        if ldr_oscuro_raw is None:
            ldr_oscuro_raw = self.ldr_oscuro_raw
        if ldr_luz_raw is None:
            ldr_luz_raw = self.ldr_luz_raw
        raw = sum(self.adc.read() for _ in range(10)) / 10
        return pct(raw, ldr_oscuro_raw, ldr_luz_raw)