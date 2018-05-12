''' Adafruit/IO interface for Weather Station Contrator

revision history
----------------
2018-03-03    liangc    - draft
'''

import os
import sys
import serial
import re
from datetime import datetime
import sqlite3

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
    """Parse weather hub line, and return a map of sensor data
    [addr, rssi, cpu-temp, cpu-volt, temp, pre, hum]: 0x00124b000e09465a, 241, 22, 598, 2222, 9736161, 46366
    """
    matched = re.match(r'\[.*\]: (0x[0-9a-fA-F]+), ([-+]?\d+), (\d+), (\d+), (\d+), (\d+), (\d+)', line)
    if matched == None:
        sys.stdout.write("no match!\n")
        raise RuntimeError("Unable to parse input line!")
    return matched.group(0), matched.group(1), matched.group(2),matched.group(3), matched.group(4), matched.group(5), matched.group(6), matched.group(7)    

sqlite_file = "/home/pi/iot_server/iot_sensor_data.db"
sensor_table = "sensor_data"
serial_port = '/dev/serial0'
serial_baud = 115200

#addr = 0x00124b000e09465a, rssi = -36, cpu_temp = 19.00, battery_volt = 2.34, temp = 21.08, pressure = 977.6121, humidity = 37.77

def create_sensor_data_table():
    # setup database
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    
    sql = 'create table if not exists ' + sensor_table \
        + '(tm timestamp default current_timestamp, ' \
        + ' addr char(18), ' \
        + ' rssi integer,  '\
        + ' cpu_temp decimal(5,2),'\
        + '  battery_volt decimal(3,2), '\
        + ' temp decimal(5,2),' \
        + ' pressure decimal(8,4), '\
        + ' humidity decimal(5,2) '\
        + ')'
            
    c.execute(sql)
    c.close()
    conn.close()
    
def main3():
    create_sensor_data_table()
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    
    insert_stmt = 'insert into ' + sensor_table \
        + '(addr, rssi, cpu_temp, battery_volt, temp, pressure, humidity)' \
        + "values('0x1234', -20, 23, 3.25, 22.34, 837.231, 64.32)"
        
    c.execute(insert_stmt)
    conn.commit()
    conn.close()

def main():
    sys.stdout.write("Open database %s.\n" % sqlite_file)
    sys.stdout.flush()
    create_sensor_data_table()
    
    conn = sqlite3.connect(sqlite_file)
    
    insert_stmt_stem = 'insert into ' + sensor_table \
        + '(addr, rssi, cpu_temp, battery_volt, temp, pressure, humidity)' \
        + "values(%s, %d, %d, %.2f, %.2f, %.4f, %.2f)"
        
    sys.stdout.write("Open serial port %s with baud rate %d.\n" % (serial_port, serial_baud))
    sys.stdout.flush()
    # open port to the concentrator of weather hub
    #   serial config: 115200/8/N/1
    #// hub_serial = serial.Serial('/dev/ttyACM2', 115200)
    hub_serial = serial.Serial(serial_port, serial_baud)

    sys.stdout.write("Open Adafruit IO.\n")
    sys.stdout.flush()
    # Set to your Adafruit IO key.
    io_client_key = get_ioclient_key()
    # Create an instance of the REST client.
    aio = Client(io_client_key)
    
    # simple regex pattern to parse signed/unsigned integers    
    hub_info_pattern = re.compile('[-+]?[0-9]+') 
    
    send_to_adafruit = False
    
    sys.stdout.write(str(datetime.now()))
    sys.stdout.write("Waiting for IoT Hub...\n")
    sys.stdout.flush()
    
    while True:
        try:
            line = hub_serial.readline()
            sys.stdout.write('line: ' + line)
            data = parse_line(hub_info_pattern, line)
            #sys.stdout.write( type(data) )
            #sys.stdout.write( data )
            if len(data) != 8:
                raise ValueError('Oops, invalid input from concentrator, # of data was %d!' % len(data))
            # sys.stdout.write('%s :' % str(datetime.now()))
            sys.stdout.write('addr = %s, ' % data[1])
            sys.stdout.write('rssi = %d, '% int(data[2]))
            sys.stdout.write('cpu_temp = %.2f, ' % (int(data[3])/1.0))
            sys.stdout.write('battery_volt = %.2f, ' % (int(data[4])/256.0)) 
            sys.stdout.write('temp = %.2f, ' % (int(data[5])/100.0))
            sys.stdout.write('pressure = %.4f, ' % (int(data[6])/10000.0))
            sys.stdout.write('humidity = %.2f' % (int(data[7])/1000.0))
            sys.stdout.write('\n')
            
            # write data into table
            c = conn.cursor()
            insert_stmt = insert_stmt_stem % (data[1], int(data[2]), int(data[3])/1.0, int(data[4])/256.0, int(data[5])/100.0, int(data[6])/10000.0, int(data[7])/1000.0)
            c.execute(insert_stmt)
            conn.commit()
        
            if send_to_adafruit:
                aio.send('rssi', int(data[2]))
                aio.send('cpu_temp', int(data[3])/1.0)
                aio.send('battery_volt', int(data[4])/256.0) 
                aio.send('temp', int(data[5])/100.0)
                aio.send('pressure', int(data[6])/10000.0)
                aio.send('humidity', int(data[7])/1000.0)
                
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write('Oops, exception: ')
            print( e )    

if __name__ == "__main__":
    main()


