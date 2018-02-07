#!/usr/bin/env python
# encoding=utf8
'''
    File name: get_temp.py
    Description: Get temperature from DHT22 sensor and upload the information to WeatherUnderground.
    Python Version: 2.7.13
'''
__author__ = "Alberto Andrés"
__license__ = "GPL"

dth22_sensor = True
#WEATHER_UPLOAD = False
log_file = True
#dth22_sensor = False
WEATHER_UPLOAD = True
#log_file = False
#log_gspread = False
log_gspread = True

import time
import json
import urllib2
import gspread
from config import Config
from urllib import urlencode
from time import sleep
from oauth2client.service_account import ServiceAccountCredentials

UTC_offset = 1

if dth22_sensor:
    import Adafruit_DHT

def c_to_f(input_temp):
    # convert input_temp from Celsius to Fahrenheit
    return (input_temp * 1.8) + 32

def parse_pws_conditions_json(pws, alb_key):
    # parse json conditions from weather station
    f = urllib2.urlopen('http://api.wunderground.com/api/'+alb_key+'/conditions/q/pws:'+pws+'.json')
    json_string = f.read()
    parsed_json = json.loads(json_string)
    f.close()
    return parsed_json
    
def read_temp_c_from_pws(parsed_json):
    # read temperature from a weather station
    temp_c = parsed_json['current_observation']['temp_c']
    return temp_c
    
def read_wind_from_pws(parsed_json):
    # read win direcction from a weather station
    wind_dir = parsed_json['current_observation']['wind_dir']
    windspeedmph = parsed_json['current_observation']['wind_mph']
    windgustmph = parsed_json['current_observation']['wind_gust_mph']
    return wind_dir, windspeedmph, windgustmph
    
def read_rain_from_pws(parsed_json):
    # read win direcction from a weather station
    precip_1hr_in = parsed_json['current_observation']['precip_1hr_in']
    precip_today_in = parsed_json['current_observation']['precip_today_in']
    return precip_1hr_in, precip_today_in

def get_local_date():
    # get local date with UTC timezone offset
    if (time.strftime('%H') == '23'):
        day = str(int(time.strftime('%d')) + UTC_offset)
    else:
        day = time.strftime('%d')
        
    local_date = time.strftime('%Y-%m-') + day
    return local_date

def get_local_time():
    # get local time with UTC timezone offset
    hh = str(int(time.strftime('%H')) + UTC_offset)
    if (hh == '24'):
        hh = '00'
    mm = time.strftime('%M')
    local_time = hh + ':' + mm
    return local_time
    
# ============================================================================
#  Read Weather conditions from WU stations or DTH22 sensor
# ============================================================================
alb_key = 'cac064240e1597b3'
pws_1 = 'IGULAEST2'
pws_2 = 'IGUADALA26'
pws_3 = 'IMARCHAM2'
json_pws_1 = parse_pws_conditions_json(pws_1,alb_key)
json_pws_2 = parse_pws_conditions_json(pws_2,alb_key)
json_pws_3 = parse_pws_conditions_json(pws_3,alb_key)

location = json_pws_1['current_observation']['observation_location']['city']
pressure_mb = json_pws_1['current_observation']['pressure_mb']
wind_dir, windspeedmph, windgustmph = read_wind_from_pws(json_pws_1)
rainin, dailyrainin = read_rain_from_pws(json_pws_1)
hum = None
temp_c = None
n_retries = 0

if dth22_sensor:
    # DTH22 sensor is enabled

    # Adafruit_DHT.DHT22
    sensor = Adafruit_DHT.DHT22
    
    # Raspberry Pi with DHT sensor connected to GPIO23 (Pin 16).
    pin = 23
    
    # Try to grab a sensor reading.  Use the read_retry method which will retry up
    # to 15 times to get a sensor reading (waiting 2 seconds between each retry).
    while (hum == None and temp_c == None) or n_retries == 15:
        hum, temp_c = Adafruit_DHT.read_retry(sensor, pin)
        n_retries += 1
        print 'Ret: ',n_retries
        sleep(1)
    # correct DHT22 error
    temp_c -= 0.5
    dewpoint = float((hum**(1./8) * (112 + 0.9 * temp_c)) + (0.1 * temp_c) - 112)
    
else:
    # DTH22 sensor is disabled

    hum = json_pws_1['current_observation']['relative_humidity']
    temp_c_pws_1 = read_temp_c_from_pws(json_pws_1)
    temp_c_pws_2 = read_temp_c_from_pws(json_pws_2)
    temp_c_pws_3 = read_temp_c_from_pws(json_pws_3)
    temp_c = (temp_c_pws_1 + temp_c_pws_2 + temp_c_pws_3) / 3

    # Calculate dewpoint as hum^(1/8) * (112 + 0.9 * temp_c) + (0.1 * temp_c - 112)
    hum_float = float(float(hum.strip('%'))/100)
    dewpoint = float((hum_float**(1./8) * (112 + 0.9 * temp_c)) + (0.1 * temp_c) - 112)
print "\nCurrent temperature and humidity in %s is: %s %s" % (location, temp_c, hum)



# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print("\n\bInitializing Weather Underground configuration\n")
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
if (wu_station_id is None) or (wu_station_key is None):
    print("Missing values from the Weather Underground configuration file\n")
    sys.exit(1)

# we made it this far, so it must have worked...
print("Successfully read Weather Underground configuration values")
print('Station ID:', wu_station_id)
# print('Station key:', wu_station_key)

# ========================================================
# Upload the weather data to Weather Underground
# PWS: https://www.wunderground.com/personal-weather-station/dashboard?ID=IGUADALA36&cm_ven=localwx_pwsdash#history
# API Info:
# http://api.wunderground.com/api/cac064240e1597b3/conditions/q/pws:IGULAEST2.json
# ========================================================
WU_URL = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
# is weather upload enabled (True)?
if WEATHER_UPLOAD:
    # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
    print("\n --> Uploading data to Weather Underground...\n")
    # build a weather data object
    weather_data = {
        "action": "updateraw",
        "ID": wu_station_id,
        "PASSWORD": wu_station_key,
        "windir": wind_dir,
        "windspeedmph": windspeedmph,
        "windgustmph": windgustmph,
        "rainin": rainin,
        "dailyrainin": dailyrainin,
        "dateutc": "now",
        "tempf": str(c_to_f(temp_c)),
        "humidity": hum,
        "dewptf": str(c_to_f(dewpoint)),
        "baromin": pressure_mb,
    }
    try:
        upload_url = WU_URL + "?" + urlencode(weather_data)
        response = urllib2.urlopen(upload_url)
        html = response.read()
        print("Server response:", html)
        # do something
        response.close()  # best practice to close the file
    except:
        print("Exception:", sys.exc_info()[0], SLASH_N)
else:
    print("Skipping Weather Underground upload")
    
if log_file:
    fd = open('/home/pi/alberweatherstation/log_temp.txt', 'a')
    fd.write('\n'+time.strftime('%l:%M %p %Y-%b-%d: ')+str(temp_c).replace(".",","))
    fd.close

if log_gspread:
    # use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name('/home/pi/alberweatherstation/alberWS-e51a8476d2f4.json', scope)
    client = gspread.authorize(creds)
    # Find a workbook by name and open the first sheet
    # Make sure you use the right name here.
    sheet = client.open("alberws").sheet1
    # insert a new row
    time_str = time.strftime('%Y-%m-%d: %p %X')
    row = [get_local_date(),get_local_time(),format(temp_c,'.2f').replace(".",","),format(hum, '.2f').replace(".",",")]
    index = 2
    sheet.insert_row(row, index)
    

