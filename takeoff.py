__description__ = 'Class to evaluate and track downloading of samples'
__author__ = 'Brandon Dixon'
__version__ = '1.0'
__date__ = '2012/05/02'

try:
	from lib.jetplane import *
	import sys
	import time
except ImportError, e:
	print str(e)
	sys.exit(1)

f = open("small_cc","r")
lines = f.readlines()
f.close()

errors = []

for x in range(0,100):
	for line in lines:
		cc = line.strip()
		b52 = jetplane("127.0.0.1","8118",True,"INFO")
		res = b52.take_off(cc,25)
