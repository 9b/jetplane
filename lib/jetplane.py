__description__ = 'Class to go through and test the IP address assigned by TOR'
__author__ = 'Brandon Dixon'
__version__ = '1.0'
__date__ = '2012/09/08'

try:
	import datetime
	import random
	import re
	import logging
	import sys	
	import requests
	import socket
	import time
	import os
	from subprocess import Popen, PIPE, STDOUT
	from cymruwhois import Client
	from mongodb import *
except ImportError, e:
	print str(e)
	sys.exit(1)

class jetplane:
	def __init__(self,host,port,db=False,logging="_"):
		self._log = utility.logger("jetplane",logging)
		self._host = host
		self._port = port
		self._proxy_ip = None
		self._whois_handle = Client()
		self._criteria = None
		self._max_tours = 0
		self._tours = 1
		self._takeoff_time = None
		self._errors = 0
		self._success = False
		self._trip_details = []
		self._db = db
		self._kill_bit = False

		if self._db:
			self._mongodb_handle = mongodb("127.0.0.1","27017","jetplane","hanger","INFO")
			self._mdb = self._mongodb_handle.get_con()

	def take_off(self,criteria,tours):
		self._takeoff_time = time.time()
		self._max_tours = tours + 1
		self._criteria = criteria.lower()
		self._log.info("Trip details: max tours - %d, local - %s" % (self._max_tours,self._criteria))
		r = self._world_tour()
		return r

	def _world_tour(self):
		self._log.info("Baggage check number %d" % self._tours)
		time.sleep(3) #naptime
		self._log.info("Tickets purchased to %s" % self._criteria)
		self._flush_addr() #kill off any address we had before
		self._log.info("Safety and pre-flight checks")
		time.sleep(7)

		#accept 3 errors before ditching
		for i in range(0,2): 
			prox_run = self._proxy_check() #see what TOR gave us
			if prox_run:
				break
			else:
				if i == 1:
					return False

		for i in range(0,2):
			who_run = self._whoami() #pull out the decision
			if who_run:
				break
			else:
				if i == 1:
					return False

		self._decide() #did we land in the right area
		return True

	def _flush_addr(self):
		self._log.info("Boarding the plane")
		sout = Popen(['/etc/init.d/tor', 'restart'], stdout=PIPE, stderr=STDOUT).communicate()[0]

	def _proxy_check(self):
		self._headers = { 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0', 'Connection':'Keep-Alive' }
		self._proxies = { "http": self._host + ":" + self._port }
		self._urls = ['http://whatismyipaddress.com/','http://www.whatsmyip.us/','http://www.ipchicken.com/','http://www.whatsmyip.info/','http://www.whatsmyip.in/','http://www.whatsmyip.cc/','http://ipswift.com']
		self._url = self._urls[random.randint(0,len(self._urls)-1)]
		self._log.info("Fetching address data from %s" % self._url)
		response = requests.get(self._url, proxies=self._proxies)
		if response.status_code == 200:
			try:
				self._proxy_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])',response.content).group()
				self._log.info("Query returned %s" % self._proxy_ip)
				return True
			except:
				self._log.error("Failed to find IP address using %s" % self._url)
				self._errors += 1
				return False
		else:
			self._proxy_ip = "127.0.0.1"
			self._log.error("Query failed, flushing again")
			self._errors += 1
			return False
	
	def _whoami(self):
		try:
			self._whois_data = self._whois_handle.lookup(self._proxy_ip)
			self._addr_owner = self._whois_data.owner
			self._addr_asn = self._whois_data.asn
			self._addr_prefix = self._whois_data.prefix
			self._addr_cc = self._whois_data.cc
			return True
		except Exception, e:
			self._log.error("Failed to gather WHOIS for %s" % self._proxy_ip)
			self._log.info(str(e))
			self._errors += 1
			return False

	def _trip_log(self):

		if not self._kill_bit:
			if self._mongodb_handle._not_processed(self._criteria):
				init_obj = { 'location':self._criteria,'trips':[],'total_successful_trips':0,'total_trips':0 }
				self._mongodb_handle._insert_full(init_obj)
				trip_obj = { 'trip_date':datetime.datetime.utcnow(),'success':self._success,'error_count':self._errors,'total_stops':self._tours - 1,'trip_details':self._trip_details,'trip_time':str(time.time() - self._takeoff_time),'max_stops':self._max_tours -1 }
				self._mongodb_handle._add_trip(self._criteria,trip_obj)
			else:
				trip_obj = { 'trip_date':datetime.datetime.utcnow(),'success':self._success,'error_count':self._errors,'total_stops':self._tours - 1,'trip_details':self._trip_details,'trip_time':str(time.time() - self._takeoff_time),'max_stops':self._max_tours -1 }
				self._mongodb_handle._add_trip(self._criteria,trip_obj) 
			
			self._kill_bit = True
		else:
			return True

	def _decide(self):

		def trip_complete():
			self._success = True
			if self._db:
				self._trip_log()

			self._log.info("You are free to move about the country")
			self._log.info("Your credentials: %s" % self._whois_data)
			self._log.info("Total flight time: %s, Places visited: %d" % (str(time.time() - self._takeoff_time),self._tours))

		def keep_going():
			self._log.info("Landed in %s. Back on the plane, wrong stop" % self._addr_cc)
			self._tours += 1
			if self._max_tours <= self._tours:
				self._no_fly()
			else:
				self._world_tour()

		details_obj = { 'stop_number':self._tours,'location':self._addr_cc,'owner':self._addr_owner,'asn':self._addr_asn,'network':self._addr_prefix,'ip_address':self._proxy_ip }
		self._trip_details.append(details_obj)

		if len(self._criteria) == 2:
			if self._addr_cc.lower() == self._criteria.lower():
				trip_complete()
			else:
				keep_going()

		else: #looks like we are heading to a company
			r = re.compile(self._criteria,re.IGNORECASE)
			found = r.search(self._addr_owner)
			if found != None:
				trip_complete()
			else:
				keep_going()

	def _no_fly(self):
		self._success = False

		if self._db:
			self._trip_log()

		self._log.info("Unable to find any flights to %s, please pick another" % self._criteria)
