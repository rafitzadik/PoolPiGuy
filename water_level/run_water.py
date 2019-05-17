# I prefer to turn the solenoid valve on and off in a stand-alone
# process. The chances for error that would leave the water running
# forever are lower, and if the process exits then the water would stop

import gpiozero, time
from pathlib import Path

# This file would signal to other programs that water is running.
# Also if it gets deleted by an external program,
# we will stop the water and exit.

running_file = Path('/home/pi/poolpi/water_level/water_running_runs')
timeToRun = 1800 #time to run water in seconds

f = running_file.open('w')
f.close()
dev = gpiozero.DigitalOutputDevice(26, initial_value = True)
startTime = time.time()
dev.off() #this is what turns water on, strangely...
while (time.time() - startTime) < timeToRun:
    time.sleep(1)
    if (not running_file.exists()):
        break
dev.on()
running_file.unlink()
