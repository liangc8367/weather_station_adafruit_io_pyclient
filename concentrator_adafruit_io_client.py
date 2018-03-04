''' Adafruit/IO interface for Weather Station Contrator

revision history
----------------
2018-03-03    liangc    - draft
'''

import os
import sys
import serial
import re
from Adafruit_IO import Client, Data, Feed, Group, RequestError

def get_ioclient_key():
    """Return the AIO key specified in the ADAFRUIT_IO_KEY environment
    variable, or raise an exception if it doesn't exist.
    """
    key = os.environ.get('ADAFRUIT_IO_KEY', None)
    if key is None:
        raise RuntimeError("ADAFRUIT_IO_KEY environment variable must be " \
          "set with valid Adafruit IO key to run this test!")
    return key

def get_ioclient_username():
    """Return the AIO username specified in the ADAFRUIT_IO_USERNAME
    environment variable, or raise an exception if it doesn't exist.
    """
    username = os.environ.get('ADAFRUIT_IO_USERNAME', None)
    if username is None:
        raise RuntimeError("ADAFRUIT_IO_USERNAME environment variable must be " \
          "set with valid Adafruit IO username to run this test!")
    return username

def parse_line(pattern, line):
    """Parse weather hub line, and return a map of sensor data"""
    data = pattern.findall(line)
    return data    


# simple regex pattern to parse signed/unsigned integers    
hub_info_pattern = re.compile('[-+]?[0-9]+') 

# Set to your Adafruit IO key.
io_client_key = get_ioclient_key()
# Create an instance of the REST client.
aio = Client(io_client_key)

# open port to the concentrator of weather hub
#   serial config: 115200/8/N/1
hub_serial = serial.Serial('/dev/ttyACM2', 115200)
send_to_adafruit = True

while True:
    try:
        line = hub_serial.readline()
        sys.stdout.write('line: ' + line)
        data = parse_line(hub_info_pattern, line)
        if len(data) != 7:
            raise ValueError('Oops, invalid input from concentrator, # of data was %d!' % len(data))
        
        sys.stdout.write('rssi = %d, '% int(data[1]))
        sys.stdout.write('cpu_temp = %.2f, ' % (int(data[2])/1.0))
        sys.stdout.write('battery_volt = %.2f, ' % (int(data[3])/256.0)) 
        sys.stdout.write('temp = %.2f, ' % (int(data[4])/100.0))
        sys.stdout.write('pressure = %.4f, ' % (int(data[5])/10000.0))
        sys.stdout.write('humidity = %.2f' % (int(data[6])/1000.0))
        sys.stdout.write('\n')
    
        if send_to_adafruit:
            aio.send('rssi', int(data[1]))
            aio.send('cpu_temp', int(data[2])/1.0)
            aio.send('battery_volt', int(data[3])/256.0) 
            aio.send('temp', int(data[4])/100.0)
            aio.send('pressure', int(data[5])/10000.0)
            aio.send('humidity', int(data[6])/1000.0)
    except Exception, e:
        sys.stdout.write('Oops, exception: ')
        print e
# # Send a value to the feed 'Test'.  This will create the feed if it doesn't
# # exist already.
# aio.send('Test', 42)


