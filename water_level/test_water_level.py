#move to the correct virtualenv
activate_this_file = "/home/pi/.virtualenvs/webserv/bin/activate_this.py"
exec(open(activate_this_file).read(), {'__file__': activate_this_file})


import gpiozero
import time
import requests
import datetime

#regrettably the more complex "hold" recepies of gpiozero don't work well for me. They sometimes fail to activate.
#hence writing my own, possibly not as precise, de-bouncer.

STATE_FILE_PATH = '/home/pi/poolpi/water_level/status.txt'
def notification(text):
    ifttt_url = open('/home/pi/poolpi/water_level/ifttt_url.txt').readline().rstrip() #get the IFTTT URL
    try:
        r = requests.post(ifttt_url, json={"value1":text})
    except:
        print('request to {} with value1 {} failed'.format(ifttt_url, text))

def water_level_low():
    print('Water Level Low!!')
    stateFile = open(STATE_FILE_PATH, 'w')
    stateFile.write('Water Level Low!!')
    stateFile.close()
    notification("Water Level LOW!!")

def water_level_hi():
    print('water level hi')
    stateFile = open(STATE_FILE_PATH, 'w')
    stateFile.write('Water Level High :)')
    stateFile.close()
    notification("Water Level Hi :)")

#main:        
level_input = gpiozero.Button(16, bounce_time = 2.0)
water_low = level_input.is_pressed
if (water_low):
    water_level_low()
else:
    water_level_hi()

print('Initialized')

debounce_count = 0
debounce_max = 3
while(True):
    new_input = level_input.is_pressed
    if water_low: #look for multiple consequtive new_input==False
        if new_input: #so we still see a water_low reading
            if (debounce_count > 0):
                print('resetting debounce_count')
            debounce_count = 0
        else: #we see a NOT water_low:
            debounce_count += 1
            print('incremented debounce_count to {}'.format(debounce_count))
            if (debounce_count >= debounce_max):
                water_low = False
                debounce_count = 0
                water_level_hi()
    else: #look for multiple consequtive new_input == True
        if not new_input: #so we still see a NOT water_low (ie water hi)
            if (debounce_count > 0):
                print('resetting debounce_count')
            debounce_count = 0
        else: #we see a water_low:
            debounce_count += 1
            print('incremented debounce_count to {}'.format(debounce_count))
            if (debounce_count >= debounce_max):
                water_low = True
                debounce_count = 0
                water_level_low()
    time.sleep(1)
        
    
print('Exiting')
    
