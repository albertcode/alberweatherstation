import urllib2
import json
from config import Config
from urllib import urlencode
import random

def c_to_f(input_temp):
    # convert input_temp from Celsius to Fahrenheit
    return (input_temp * 1.8) + 32


alb_key = 'cac064240e1597b3'

	f = urllib2.urlopen('http://api.wunderground.com/api/'+alb_key+'/conditions/q/pws:IGULAEST2.json')
	f2 = urllib2.urlopen('http://api.wunderground.com/api/'+alb_key+'/conditions/q/pws:IGUADALA26.json')
	f3 = urllib2.urlopen('http://api.wunderground.com/api/'+alb_key+'/conditions/q/pws:IGUADALA29.json')

json_string = f.read()
parsed_json = json.loads(json_string)
location = parsed_json['current_observation']['observation_location']['city']
temp_c = parsed_json['current_observation']['temp_c']
pressure_mb = parsed_json['current_observation']['pressure_mb']
hum = parsed_json['current_observation']['relative_humidity']
print "\nCurrent temperature and humidity in %s is: %s %s" % (location, temp_c, hum)
f.close()

# ============================================================================
#  Read Weather Underground Configuration Parameters
# ============================================================================
print("\nInitializing Weather Underground configuration")
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
	print("Uploading data to Weather Underground")
	# build a weather data object
	weather_data = {
		"action": "updateraw",
		"ID": wu_station_id,
		"PASSWORD": wu_station_key,
		"dateutc": "now",
		"tempc": temp_c,
		"tempf": str(c_to_f(temp_c)),
		"humidity": hum,
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




