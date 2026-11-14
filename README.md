# Mini invernadero inteligente con ESP32-S3

Proyecto final de Programación II (Universidad CES, 2026). Un mini invernadero que mide humedad del suelo, temperatura, humedad del aire y luz, y decide solo cuándo regar, ventilar o encender las luces. Cada 5 segundos envía los datos a un servidor para mostrarlos en un dashboard.

## ¿Qué hace?

| Qué mide | Sensor | Qué decide |
|---|---|---|
| Humedad del suelo | YL-69 | Enciende la bomba de riego cuando baja de 35 % |
| Temperatura y humedad del aire | HTU21D (I2C) | Ventilador desde 27 °C y extractor desde 30 °C o con humedad alta |
| Luz ambiental | LDR | Ajusta con PWM la intensidad de los LEDs de crecimiento |

Los ventiladores usan **histéresis** (por ejemplo, encienden a 27 °C y apagan bajo 26 °C) para no prender y apagar sin parar cerca del límite.

Además:
- Una pantalla LCD 16x2 (I2C) muestra los datos en 4 páginas que rotan cada 3 segundos.
- LEDs indicadores muestran el estado de temperatura y humedad.
- Se calculan métricas en vivo: temperatura promedio, máxima y mínima, número de riegos y tiempo activo.
- Los datos se envían como JSON por HTTP (`POST /api/datos`) cada 5 segundos.

## Hardware

- ESP32-S3
- Sensor de humedad de suelo YL-69
- Sensor de temperatura y humedad HTU21D
- Fotorresistencia (LDR)
- 3 relés (bomba, ventilador, extractor) con transistores NPN
- Registro de desplazamiento 74HC595 (para ampliar salidas)
- LEDs indicadores y LEDs de crecimiento con PWM
- Pantalla LCD 16x2 con módulo I2C

## Cómo está organizado el código

Está escrito en **MicroPython** con programación orientada a objetos y `uasyncio`, para que la lectura de sensores, el envío de datos y la pantalla corran al mismo tiempo.

| Archivo | Qué contiene |
|---|---|
| `main.py` | Clase `Invernadero` con la lógica de control, métricas y cliente IoT |
| `yl69.py` | Sensor de humedad del suelo con calibración |
| `htu21d.py` | Driver del sensor de temperatura y humedad |
| `ldr.py` | Sensor de luz |
| `salida_digital.py` | Relés, bomba de riego, ventiladores e indicadores |
| `salida_pwm.py` | Control de LEDs por PWM |
| `expansor.py` | Control del registro 74HC595 |
| `lcd.py` y `pantalla.py` | Driver de la LCD y páginas de información |
| `entrada_analoga.py` y `entrada_digital.py` | Clases base para entradas |

## Cómo usarlo

1. Copia los archivos `.py` a la ESP32-S3 (por ejemplo con `mpremote` o Thonny).
2. Copia `config_example.py` como `config.py` y pon los datos de tu red WiFi y la IP del servidor.
3. Reinicia la placa. Empieza a medir y a enviar datos.

## Qué aprendí
- A estructurar un proyecto embebido con clases y no con un solo script largo.
- A calibrar sensores analógicos y a usar histéresis para evitar oscilaciones.
- A manejar varias tareas a la vez con `uasyncio` y a conectar un dispositivo a un servidor por HTTP.
