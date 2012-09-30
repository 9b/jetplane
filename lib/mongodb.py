__description__ = 'Class to connect to Mongo tracking DB'
__author__ = 'Brandon Dixon'
__version__ = '1.0'
__date__ = '2012/09/10'

try:
	import logging
	import sys
	import pymongo
	import datetime
	from pymongo import Connection

	from utility import *
#	from notify import *
except ImportError, e:
	from notify import *
	notify("Failed to import all libs",str(e),"INFO",True)

class mongodb:
	def __init__(self,host,port,database,collection,logging="_"):
		self._host = host
		self._port = int(port)
		self._database = database
		self._collection = collection
		self._log = utility.logger("aircontrol",logging)

		self._connect_db()

	def get_con(self):
		return self._collection

	def _connect_db(self):
		connection = Connection(self._host, self._port)
		db = connection[self._database]
		self._db = db
		collection = db[self._collection]
		self._collection = collection

	def _not_processed(self,location):
		res = self._collection.find({"location":location}).count()
		if res >= 1:
			self._log.info("Location already processed")
			return False
		else:
			self._log.info("Location added to the DB")
			return True

	def _insert_full(self,full):
		try:
			res = self._collection.insert(full) #add safe checks to this
		except Exception, exc:
			self._log.error("Failed to insert chunk into MongoDB")

	def _update_chunk(self,domain):
		try:
			res = self._collection.update({"domain":domain},{"$set": { "last_check" : datetime.datetime.utcnow() } })
		except Exception, exc:
			self._log.error("Failed to update timestamp for %s" % domain)

	def _add_trip(self,location,trip):
		try:
			res = self._collection.update({"location":location},{"$push": { "trips" : trip } } )
			self._collection.update({"location":location},{"$inc": { "total_trips" : 1 } })
			if trip['success']:
				self._collection.update({"location":location},{"$inc": { "total_successful_trips" : 1 } })
		except Exception, exc:
			self._log.error("Failed to add trip for %s" % location)
