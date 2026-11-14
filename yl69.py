from machine import Pin, ADC
 
 
class YL69:
 
    def __init__(self, pin, valor_seco=4095, valor_mojado=1500, muestras=10):
        self._adc = ADC(Pin(pin))
        self._adc.atten(ADC.ATTN_11DB)      # rango 0 - 3.3 V
        self.valor_seco = valor_seco        # lectura cruda al aire
        self.valor_mojado = valor_mojado    # lectura cruda sumergido en agua
        self.muestras = muestras
 
    def leer_valor(self):
        suma = 0
        for _ in range(self.muestras):
            suma += self._adc.read()
        return suma // self.muestras
 
    def leer_porcentaje(self):
        crudo = self.leer_valor()
        rango = self.valor_seco - self.valor_mojado
        if rango <= 0:
            return 0.0
        porcentaje = (self.valor_seco - crudo) * 100 / rango
        return max(0.0, min(100.0, porcentaje))

    def leer(self):
        return self.leer_porcentaje()
 
    # ---------- Calibración ----------
    def calibrar_seco(self):
        self.valor_seco = self.leer_valor()
        return self.valor_seco
 
    def calibrar_mojado(self):
        self.valor_mojado = self.leer_valor()
        return self.valor_mojado
 
 
# Prueba rápida / calibración desde la consola (Thonny):
#   s = YL69(34)
#   s.calibrar_seco()        # sensor al aire
#   s.calibrar_mojado()      # sensor en agua
#   s.leer_porcentaje()