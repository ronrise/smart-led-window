import pigpio
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--pin', required=True, type=int)
parser.add_argument('--brightness', required=True, type=int)

args = parser.parse_args()

if args.brightness > 255 or args.brightness < 0:
    print 'Brightness out of range 0-255'
    exit(1)

pi = pigpio.pi()

pi.set_PWM_dutycycle(args.pin, args.brightness)
