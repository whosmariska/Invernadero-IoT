from machine import Pin, PWM


class SalidaPWM:
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin), freq=1000)
        self.duty_pct = 0
        self.fijar(0)
 
    def fijar(self, porcentaje):
        self.duty_pct = porcentaje
        self.pwm.duty(int(porcentaje * 1023 / 100))
 
    def actualizar(self, luz_pct):
        if luz_pct < 25:
            self.fijar(100)
        elif luz_pct < 50:
            self.fijar(70)
        elif luz_pct < 75:
            self.fijar(40)
        else:
            self.fijar(0)
 