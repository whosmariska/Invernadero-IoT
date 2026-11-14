import asyncio


from lcd import LCDI2C


class PantallaLCD:
    GRADO = chr(0xDF)   # símbolo ° de la ROM del HD44780

    def __init__(self, lcd, invernadero):
        self.lcd, self.inv = lcd, invernadero

    @classmethod
    def crear(cls, i2c, invernadero, lcd_dirs=(0x27, 0x3F), lcd_cols=16, lcd_rows=2):
        """Busca la LCD en el bus; si no está, el proyecto sigue sin pantalla."""
        encontrados = i2c.scan()
        print("Dispositivos I2C:", [hex(a) for a in encontrados])
        for a in lcd_dirs:
            if a in encontrados:
                return cls(LCDI2C(i2c, a, lcd_cols, lcd_rows), invernadero)
        print("LCD no encontrada: revisa cableado/dirección")
        return None
 
    @staticmethod
    def _f(v, dec=1):
        return "--" if v is None else ("%." + str(dec) + "f") % v
 
    @staticmethod
    def _oo(b):
        return "ON" if b else "OFF"
 
    def _paginas(self, e):
        f, oo, g = self._f, self._oo, self.GRADO
        s = e.get("uptime_s", 0)
        return [
            ("T:%s%sC HR:%s%%" % (f(e.get("temperatura")), g, f(e.get("humedad_aire"), 0)),
             "Su:%s%% Luz:%s%%" % (f(e.get("humedad_suelo"), 0), f(e.get("iluminacion"), 0))),
            ("Bom:%s Ven:%s" % (oo(e.get("bomba")), oo(e.get("ventilador"))),
             "Ext:%s LED:%s%%" % (oo(e.get("extractor")), e.get("pwm_leds", 0))),
            ("Prom:%s%sC" % (f(e.get("prom_temp")), g),
             "Mx:%s Mn:%s" % (f(e.get("temp_max")), f(e.get("temp_min")))),
            ("Riegos:%s Ev:%s" % (e.get("riegos", 0), e.get("eventos_vent", 0)),
             "Activo:%dm %ds" % (s // 60, s % 60)),
        ]
 
    async def tarea(self, lcd_seg_por_pagina=3):
        pagina = 0
        while True:
            if self.inv.estado:
                try:
                    paginas = self._paginas(self.inv.estado)
                    l1, l2 = paginas[pagina % len(paginas)]
                    self.lcd.linea(0, l1)
                    self.lcd.linea(1, l2)
                except OSError:
                    print("Error I2C en la LCD")
            pagina += 1
            await asyncio.sleep(lcd_seg_por_pagina)