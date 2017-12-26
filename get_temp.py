#!/usr/bin/env python
import json
import urllib2
from config import Config
from urllib import urlencode
import random

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

alb_key = 'cac064240e1597b3'
pws_1 = 'IGULAEST2'
pws_2 = 'IGUADALA26'
pws_3 = 'IMARCHAM2'
json_pws_1 = parse_pws_conditions_json(pws_1,alb_key)
json_pws_2 = parse_pws_conditions_json(pws_2,alb_key)
json_pws_3 = parse_pws_conditions_json(pws_3,alb_key)
temp_c_pws_1 = read_temp_c_from_pws(json_pws_1)
temp_c_pws_2 = read_temp_c_from_pws(json_pws_2)
temp_c_pws_3 = read_temp_c_from_pws(json_pws_3)
wind_dir, windspeedmph, windgustmph = read_wind_from_pws(json_pws_1)
rainin, dailyrainin = read_rain_from_pws(json_pws_1)
 

temp_c = (temp_c_pws_1 + temp_c_pws_2 + temp_c_pws_3) / 3

location = json_pws_1['current_observation']['observation_location']['city']
pressure_mb = json_pws_1['current_observation']['pressure_mb']
hum = json_pws_1['current_observation']['relative_humidity']
print "\nCurrent temperature and humidity in %s is: %s %s" % (location, temp_c, hum)

#dewpoint = hum^(1/8) * (112 + 0.9 * temp_c) + (0.1 * temp_c - 112)
hum_float = float(float(hum.strip('%'))/100)
dewpoint = float((hum_float**(1./8) * (112 + 0.9 * temp_c)) + (0.1 * temp_c) - 112)

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
# ========================================================
WEATHER_UPLOAD = True
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
        "dewptf": dewpoint,
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
    
    
# action [action = updateraw]
# ID [ID as registered by wunderground.com]
# PASSWORD [PASSWORD registered with this ID]
# dateutc - [YYYY-MM-DD HH:MM:SS (mysql format)]
# winddir - [0-360]
# windspeedmph - [mph]
# windgustmph - [windgustmph ]
# humidity - [%]
# tempf - [temperature F]
# rainin - [rain in]
# dailyrainin - [daily rain in accumulated]
# baromin - [barom in]
# dewptf- [dewpoint F]
# weather - [text] -- metar style (+RA) 
# clouds - [text] -- SKC, FEW, SCT, BKN, OVC
# softwaretype - [text] ie: vws or weatherdisplay

