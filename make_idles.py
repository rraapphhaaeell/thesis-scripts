# -*- coding: utf-8 -*-
#make idle events from dataset: cleanrentals for idle (still containing service drives)
import csv
from operator import itemgetter
from pprint import pprint
import dateutil.parser
import datetime


FILEPATH = 'Rentals_Sample.csv'
#### IMPLEMENT REAL IDLE TIME!!

CLUSTERID = 'ClusterID.csv'

def main():
	results = []
	discard = []
	rentals = readCsv(FILEPATH)
	cl0 = []
	cl1 = []
	cl2 = []
	cl3 = []
	cl99 = []
	clusters = readCsv(CLUSTERID)
	for day in clusters:
		if day['DAYTYPE'] == '0':
			cl0.append(dateutil.parser.parse(day['DATE']).date())
		elif day['DAYTYPE'] == '1':
			cl1.append(dateutil.parser.parse(day['DATE']).date())
		elif day['DAYTYPE'] == '2':
			cl2.append(dateutil.parser.parse(day['DATE']).date())
		elif day['DAYTYPE'] == '3':
			cl3.append(dateutil.parser.parse(day['DATE']).date())
		elif day['DAYTYPE'] == '99':
			cl99.append(dateutil.parser.parse(day['DATE']).date())
# multisort
	rentals = sorted(rentals, key=lambda row: (row['VEHICLE_VIN'], row['STARTED_LOCAL']))
	#pprint(rentals[1])
	# processing
	for x in xrange(0,len(rentals)-1):
		
		thisRow = rentals[x]
		nextRow = rentals[x+1]
		
		if thisRow['VEHICLE_VIN'] == nextRow['VEHICLE_VIN']:
			thisFinished = dateutil.parser.parse(thisRow['FINISHED_LOCAL'])
			nextStarted = dateutil.parser.parse(nextRow['STARTED_LOCAL'])
			idleTime =  nextStarted - thisFinished
			appendme = {
					'VIN': thisRow['VEHICLE_VIN'],
					'DATE': thisRow['FINISHED_LOCAL'], 
					'DAYTYPE': realdaytype(thisRow['FINISHED_LOCAL'], cl0,cl1,cl2,cl3,cl99), 
					'TIMETYPE' : realtimetype(thisRow['FINISHED_LOCAL']),
					'IDLE_ADDRESS': thisRow['FINISHADDRESS'],
					'LON': thisRow['FINISHLONGITUDE'],
					'LAT': thisRow['FINISHLATITUDE'],
					'IDLEID':  str(thisRow['LOCATIONID']).zfill(2) + "%09d" % (x,),
					'IDLE_MIN': idleTime.days*1440+idleTime.seconds/60}
			discardme = {
					'VIN': thisRow['VEHICLE_VIN'],
					'LOCATIONID': thisRow['LOCATIONID'],
					'DATE': thisRow['FINISHED_LOCAL'], 
					'DAYTYPE': realdaytype(thisRow['FINISHED_LOCAL'], cl0,cl1,cl2,cl3,cl99), 
					'TIMETYPE' : realtimetype(thisRow['FINISHED_LOCAL']),
					'IDLE_ADDRESS': thisRow['FINISHADDRESS'],
					'LON': thisRow['FINISHLONGITUDE'],
					'LAT': thisRow['FINISHLATITUDE'],
					'IDLEID':  str(thisRow['LOCATIONID']).zfill(2) + "%09d" % (x,),
					'IDLE_MIN': idleTime.days*1440+idleTime.seconds/60,
					'OPSTATE_after': thisRow['OPSTATE_AFTER'],
					'OPSTATE_before': nextRow['OPSTATE_BEFORE'],
					'SERVICEDRIVE': nextRow['SERVICEDRIVE'],
					'DISTANCE': thisRow['DISTANCE'],
					'DURATION': int(thisRow['DURATION'])/60}		
##### ADD CLEANING MODE HERE: if 1,2,3,4 = true: append - else append deleted
			if thisFinished < datetime.datetime(2013,11,1):
				discardme['DISCARD'] = 'DATEERROR'
				discard.append(discardme)
				#print 'discarded: before 11.1.'
			
			
			elif thisRow['OPSTATE_AFTER'] in ['BLACK', 'GRAY', 'BLUE']:
				discardme['DISCARD'] = 'OPAFTER'
				discard.append(discardme)
				#print 'discarded: OPSTATE_AFTER'
			
			elif nextRow['OPSTATE_BEFORE'] in ['BLACK', 'GRAY', 'BLUE']:
				discardme['DISCARD'] = 'OPBEFORE'
				discard.append(discardme)
				#print 'discarded: OPSTATE_BEFORE'
			elif ( 
					nextRow['DISTANCE'] != '0' and nextRow['SERVICEDRIVE'] == '1' 
				 ):
				discardme['DISCARD'] = 'SERVICEDRIVE'
				discard.append(discardme)
				#print 'discarded: Rental Error'
			elif idleTime.seconds/60 < 0:
				discardme['DISCARD'] = 'IDLEERROR'
				discard.append(discardme)
			else:
				results.append(appendme)
				
	
	print len(results)
	print len(discard)
	writeCsv(FILEPATH, discard, suffix='Id_disc')
	writeCsv(FILEPATH, results, suffix='Idles')

def realtimetype(indate):

	indate = dateutil.parser.parse(indate).time()

	if indate <= datetime.time(05,30,00,000000):
		timetype = 'NIGHT'
	elif indate <= datetime.time(10,30,00,000000):
		timetype = 'AM'
	elif indate <= datetime.time(17,00,00,000000):
		timetype = 'NOON'
	elif indate <= datetime.time(21,30,00,000000):
		timetype = 'PM'
	elif indate <= datetime.time(23,59,59,999999):
		timetype = 'NIGHT'
	else:
		timetype = '??'
		print  '##########  ERROR  ##########'
	#timetemplate = {0:'NIGHT', 1:'NIGHT', 2:'NIGHT', 3:'NIGHT', 4:'NIGHT', 5:'NIGHT', 6:'AM', 7:'AM', 8:'AM', 9:'AM', 10:'AM', 11:'NOON', 12:'NOON', 13:'NOON', 14:'NOON', 15:'PM', 16:'PM', 17:'PM', 18:'PM', 19:'PM', 20:'PM', 21:'PM', 22:'PM', 23:'PM'}
	#timetype = timetemplate[indate.hour]
	return str(timetype)


def realdaytype(time,cl0,cl1,cl2,cl3,cl99):	
	
	if dateutil.parser.parse(time).date() in cl0:
		DT = '0'
	elif dateutil.parser.parse(time).date() in cl1:
		DT = '1'
	elif dateutil.parser.parse(time).date() in cl2:
		DT = '2'
	elif dateutil.parser.parse(time).date() in cl3:
		DT = '3'
	elif dateutil.parser.parse(time).date() in cl99:
		DT = '99'
		#remember exotic days in csv :)
	else:
		DT = '99'
	return DT					

def readCsv(filename):
	data = []
	with open(filename, 'r') as csvfile:
		reader = csv.reader(csvfile, delimiter=';')
		header = reader.next()
		for row in reader:
			dictRow = dict((header[x], row[x]) for x in range(len(header)))
			# maybe convert strings to numbers etc.
			data.append(dictRow)
	return data


def writeCsv(filename, data, suffix='out'):
	newFilename = filename.replace('.csv', ('.%s.csv' % suffix))
	with open(newFilename, 'wb') as csvfile:
		writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		header = data[0].keys()
		writer.writerow(header)
		for row in data:
			writer.writerow(row.values())


if __name__ == '__main__':
	main()