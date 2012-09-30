import pymongo
from pymongo import Connection
from time import time

def connect_to_mongo(host, port, database, collection):
	connection = Connection(host, port)
	db = connection[database]
	collection = db[collection]
	return collection

collection = connect_to_mongo("localhost", 27017, "jetplane", "hanger")

for f in collection.find( {}, {'_id':0}):
	if f['total_successful_trips'] > 0:
		loc = f['location']
		trips = f['trips']
		tstops = []
		ttime = []

		for t in trips: #top level
			tchain = []
			total_stops = t['total_stops']
			trip_time = t['trip_time']

			if total_stops != 25:
				details = t['trip_details']
				tstops.append(total_stops)
				ttime.append(trip_time)
	
				for d in details: #trip details
					tchain.append(d['location'])

			if len(tchain) > 0:
				print loc + " " + str(total_stops) + " - " + ','.join(tchain)

		avg_success = (float(f['total_successful_trips']) / f['total_trips'] * 100)
		avg_stops = float(sum(int(x) for x in tstops)) / len(tstops)
		avg_time = float(sum(float(x) for x in ttime)) / len(ttime)
		print loc + " - success: %f, stops: %f, time: %f" % (avg_success,avg_stops,avg_time) + "\n"
