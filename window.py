import json
import pigpio
import requests
import time
import argparse

# ------------------------------------------------------------
# File:   window.py
# Author: Dan King
# Contributor: Ron Rise
#
# This script needs pigpiod to be running (http://abyz.co.uk/rpi/pigpio/)
# ------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', help='Do not set pi pin output.', nargs='?', const=True)
parser.add_argument('-d', '--debug', help='Print debug statements', nargs='?', const=True)
parser.add_argument('--config-file', help='Config file location', required=True)
parser.add_argument('-p', '--gpio-pin', help='GPIO Pinout', default=21)

args = parser.parse_args()

# Configuration

# GPIO pin number
pin = args.gpio_pin

# Brightness levels (percent)
cloudy = 20
mixed = 40
sunny = 75

# Config file, persistent configs
confFile = args.config_file

# Debug, show output
debug = args.debug

# End Config

# Load config file for cache/settings
f = open(confFile, 'r')
settings = json.loads(f.read())
f.close()

if not int(settings['auto']):
    if debug:
        print('Auto brightness disabled, exiting...')
    exit()


def fetch_weather():
    weather = requests.get('https://therisefamily.com/weather')

    if debug:
        print weather.content

    return json.loads(weather.content)


if (settings['timestamp'] + 900) < time.time():
    try:
        if debug:
            print('Getting weather data...')

        data = fetch_weather()

        # Save/cache values
        settings['auto'] = 1
        settings['weather'] = data['curcond']['icon']
        settings['weatherText'] = data['curcond']['weather']
        settings['sunrise'] = data['astro']['sunrise']
        settings['sunset'] = data['astro']['sunset']
        settings['timestamp'] = round(time.time())

        f = open(confFile, 'w')
        f.write(json.dumps(settings))
        f.close()

    except Exception:
        print "Could not persist config file."
        raise

# Set max brightness based on weather
if settings['weather'] == 'rain':
    maxBright = cloudy
elif settings['weather'] == 'clear':
    maxBright = sunny
else:
    maxBright = mixed

if debug:
    print("Weather code: " + str(settings['weather']) + " (" + settings['weatherText'] + "), Sunrise: " + settings[
        'sunrise'] + ", Sunset: " + settings['sunset'])
    print("Max brightness: " + str(maxBright))

# Current time
cTime = time.localtime()
now = time.time()

# Sunrise: start brightening 20 mins before, end 70 mins after
sunriseTime = str(cTime[0]) + '-' + str(cTime[1]) + '-' + str(cTime[2]) + ' ' + settings['sunrise']
sunriseStart = int(time.mktime(time.strptime(sunriseTime, "%Y-%m-%d %I:%M %p"))) - 1200
sunriseEnd = sunriseStart + 5400

# Sunset: start dimming 75 mins before, end 15 mins after
sunsetTime = str(cTime[0]) + '-' + str(cTime[1]) + '-' + str(cTime[2]) + ' ' + settings['sunset']
sunsetStart = int(time.mktime(time.strptime(sunsetTime, "%Y-%m-%d %I:%M %p"))) - 4500
sunsetEnd = sunsetStart + 5400

# Determine the current brightness
if sunriseStart <= now <= sunriseEnd:
    elapsed = now - sunriseStart
    percent = elapsed / 5400
    brightness = maxBright * percent
    timeOfDay = "Sunrise"

elif sunriseEnd < now < sunsetStart:
    brightness = maxBright
    timeOfDay = "Day"

elif sunsetStart <= now <= sunsetEnd:
    elapsed = sunsetEnd - now
    percent = elapsed / 5400
    brightness = maxBright * percent
    timeOfDay = "Sunset"

else:
    brightness = 0
    timeOfDay = "Night"

if debug:
    print(timeOfDay + ", Brightness: " + str(brightness * 2.55))


# Change the brightness quicker at the beginning of the
# transition, then slowing near the end
def get_change_amt(current, target):
    return round(abs(current - target) / 10) + 1


# Set the brightness gradually
pi = pigpio.pi()

if not args.dry_run:
    currentBrightness = pi.get_PWM_dutycycle(pin)
else:
    currentBrightness = 100

targetBrightness = brightness * 2.55

# Brightness increasing
if targetBrightness > currentBrightness:
    while currentBrightness <= targetBrightness:
        if not args.dry_run:
            pi.set_PWM_dutycycle(pin, currentBrightness)
        else:
            break

        amt = get_change_amt(currentBrightness, targetBrightness)

        currentBrightness = currentBrightness + amt
        time.sleep(0.05)

# Brightness decreasing
elif targetBrightness < currentBrightness:
    while currentBrightness >= targetBrightness:
        if not args.dry_run:
            pi.set_PWM_dutycycle(pin, currentBrightness)
        else:
            break

        amt = get_change_amt(currentBrightness, targetBrightness)

        currentBrightness = currentBrightness - amt
        time.sleep(0.05)
