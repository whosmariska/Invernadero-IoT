import time
import json
import network
from machine import Pin, PWM, I2C
from yl69 import YL69
from htu21d import HTU21D
from ldr import SensorLuz
from expansor import Registro595
from salida_pwm import SalidaPWM
from salida_digital import BombaRiego, Ventilador, Indicadores
from pantalla import PantallaLCD
import uasyncio as asyncio

try:
    import urequests as requests
except ImportError:
    import requests

# Datos privados (WiFi y servidor): viven en config.py, que NO se sube a GitHub
from config import WIFI_SSID, WIFI_PASS, SERVER_IP, SERVER_PORT

intervalo_envio_ms=5000

pin_sda, pin_scl = 6, 5
pin_yl69, pin_ldr = 3, 2
pin_595_ds = 7                  
pin_595_latch = 1 
pin_595_clk = 38 
pin_led_pwm = 4
sr_bomba, sr_vent, sr_extr = 0, 1, 2
sr_verde, sr_amarillo, sr_rojo = 3, 4, 5
sr_azul, sr_blanco = 6, 7
reles_activos_en_bajo = False 

lcd_dirs = (0x27, 0x3F)
lcd_cols, lcd_rows = 16, 2
lcd_seg_por_pagina = 3  

yl69_seco_raw, yl69_humedo_raw = 4095, 1500
ldr_oscuro_raw, ldr_luz_raw = 4095, 0  

t_vent_on, t_vent_off = 27.0, 26.0
t_extr_on, t_extr_off = 30.0, 28.0
suelo_seco, suelo_humedo = 35, 65
riego_duracion_ms, riego_intervalo_ms = 5000, 3000
hr_baja, hr_alta, hr_apaga_extr = 40, 65, 60

class Metricas:
    def __init__(self):
        self.t0 = time.ticks_ms()
        self.suma = 0
        self.n = 0
        self.tmax = None
        self.tmin = None
 
    def registrar_temp(self, t):
        self.suma += t
        self.n += 1
        self.tmax = t if self.tmax is None else max(self.tmax, t)
        self.tmin = t if self.tmin is None else min(self.tmin, t)
 
    @property
    def promedio(self):
        return self.suma / self.n if self.n else None
 
    @property
    def uptime_s(self):
        return time.ticks_diff(time.ticks_ms(), self.t0) // 1000

class ClienteIoT:
    def __init__(self, ip, puerto):
        self.ip, self.puerto = ip, puerto
 
    async def _post(self, cuerpo):
        r, w = await asyncio.open_connection(self.ip, self.puerto)
        try:
            req = ("POST /api/datos HTTP/1.1\r\nHost: %s\r\n"
                   "Content-Type: application/json\r\n"
                   "Content-Length: %d\r\nConnection: close\r\n\r\n%s"
                   % (self.ip, len(cuerpo), cuerpo))
            w.write(req.encode())
            await w.drain()
            await r.read(64)
        finally:
            w.close()
            await w.wait_closed()
 
    async def enviar(self, datos):
        try:
            await asyncio.wait_for(self._post(json.dumps(datos)), 3)
        except Exception as e:
            print("Envío falló:", e)  # no detiene el programa


# --------------------------------------------------PRINCIPAL------------------------------------

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        for _ in range(30):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    print("WiFi:", "ok" if wlan.isconnected() else "sin conexión")
    return wlan

class Invernadero:
    def __init__(self):
        self.suelo = YL69(pin_yl69)
        i2c = I2C(0, sda=Pin(pin_sda), scl=Pin(pin_scl), freq=100000)
        # Estado inicial: relés apagados (según su lógica) y LEDs apagados
        inicial = 0
        if reles_activos_en_bajo:
            inicial = (1 << sr_bomba) | (1 << sr_vent) | (1 << sr_extr)
        self.expansor = Registro595(pin_595_ds, pin_595_clk, pin_595_latch, inicial)
        self.ambiente = HTU21D(i2c)
        self.luz = SensorLuz(pin_ldr)
        self.bomba = BombaRiego(self.expansor, sr_bomba, riego_intervalo_ms,
                                riego_duracion_ms, suelo_seco, reles_activos_en_bajo)
        self.vent = Ventilador(self.expansor, sr_vent, t_vent_on, t_vent_off,
                               reles_activos_en_bajo)
        self.extr = Ventilador(self.expansor, sr_extr, t_extr_on, t_extr_off,
                               reles_activos_en_bajo)
        self.leds = SalidaPWM(pin_led_pwm)
        self.ind = Indicadores(self.expansor, sr_verde, sr_amarillo, sr_rojo,
                               sr_azul, sr_blanco)
        self.metricas = Metricas()
        self.cliente = ClienteIoT(SERVER_IP, SERVER_PORT)
        self.extr_por_temp = False
        self.extr_por_hum = False
        self.estado = {}
        self.pantalla = PantallaLCD.crear(i2c, self)

    def _control_ambiente(self, t, hr):
        self.vent.fijar(self.vent.pide_encender(t))

        # Extractor por temperatura (histéresis 30 / 28 °C)
        if t >= t_extr_on:
            self.extr_por_temp = True
        elif t < t_extr_off:
            self.extr_por_temp = False
        # Extractor por humedad (enciende a 65 %, apaga bajo 60 %)
        if hr >= hr_alta:
            self.extr_por_hum = True
        elif hr < hr_apaga_extr:
            self.extr_por_hum = False
        self.extr.fijar(self.extr_por_temp or self.extr_por_hum)

        self.ind.temperatura(self.vent.encendido, t >= t_extr_on)
        self.ind.humedad(hr)

    async def tarea_control(self):
        while True:
            t, hr = await self.ambiente.leer()
            hs = self.suelo.leer()
            luz = self.luz.leer()

            if t is not None:
                self.metricas.registrar_temp(t)
                self._control_ambiente(t, hr)
            self.bomba.actualizar(hs)
            self.leds.actualizar(luz)

            m = self.metricas
            self.estado = {
                "temperatura": t,
                "humedad_aire": hr,
                "humedad_suelo": hs,
                "iluminacion": luz,
                "bomba": self.bomba.encendido,
                "ventilador": self.vent.encendido,
                "extractor": self.extr.encendido,
                "pwm_leds": self.leds.duty_pct,
                "prom_temp": m.promedio,
                "temp_max": m.tmax,
                "temp_min": m.tmin,
                "riegos": self.bomba.riegos,
                "uptime_s": m.uptime_s,
                "eventos_vent": self.vent.eventos + self.extr.eventos,
            }
            print(self.estado)
            await asyncio.sleep_ms(500)

    async def tarea_envio(self):
        while True:
            await asyncio.sleep_ms(intervalo_envio_ms)
            if self.estado:
                await self.cliente.enviar(self.estado)

    async def correr(self):
        tareas = [self.tarea_control(), self.tarea_envio()]
        if self.pantalla:
            tareas.append(self.pantalla.tarea())
        await asyncio.gather(*tareas)


conectar_wifi()
asyncio.run(Invernadero().correr())

