import machine
import time
a = machine.Pin(2, machine.Pin.OUT)
while 1:
    time.sleep(1)
    a.value(not a.value())
