# -*- coding: utf-8 -*-
#rentals data cleaner 
#cleans renatal data of SERVICEDRIVES and WRONG DATES (1.1.1900) and create table for gangliniencluster
import csv
from operator import itemgetter
from pprint import pprint
import dateutil.parser
import datetime

FILEPATH = 'Rentals_Sample.csv'
HOLIDAYS = 'Holidays.csv'								#provide list with holidays for each respective bundesland!
### DATE: 31.10.2013 RAUS!!!!!
### ISt es richtig die 1900er rauszukicken? Wird verfälschte IDLE Zeiten geben. 
### Besser wäre erst im IDLE Berechnung diese rauszunehmen. Für Rentals ja erst mal egal (außer Startdate!!)


def main():
	rentals = readCsv(FILEPATH)

	holidaylist = []
	holidaycsv = readCsv(HOLIDAYS)
	for n in holidaycsv:
		holidaylist.append(dateutil.parser.parse(n['Feiertage']).date())
	
	for rowID in xrange(len(rentals)):
		thisrow = rentals[rowID]
		rentstart = dateutil.parser.parse(thisrow['STARTED_LOCAL'])
		thisrow['RENTALID'] = str(thisrow['LOCATIONID']).zfill(2) + "%09d" % (rowID,)
		thisrow['DAYTYPE'] = finddaytype(rentstart, holidaylist)
		thisrow['TIMETYPE'] = findtimetype(rentstart.time())
		
	# rentalsforidle = yearclean(rentals) 						#delete 1900er for idlecalc
	# writeCsv(FILEPATH, rentalsforidle, suffix='foridle')
	
	rentalsforstats = clean(rentals) 							#no servicedrives for rentalsforstats
	writeCsv(FILEPATH, rentalsforstats, suffix='forstats')
	tagesgangout = tagesgang(rentals)							#create table of days with rentals per hour
	writeCsv(FILEPATH, tagesgangout, suffix='tagesgang')


def findtimetype(indate):
	#insert cluster results in dict
	timetemplate = {0:'NIGHT', 1:'NIGHT', 2:'NIGHT', 3:'NIGHT', 4:'NIGHT', 5:'NIGHT', 6:'AM', 7:'AM', 8:'AM', 9:'AM', 10:'AM', 11:'NOON', 12:'NOON', 13:'NOON', 14:'NOON', 15:'PM', 16:'PM', 17:'PM', 18:'PM', 19:'PM', 20:'PM', 21:'PM', 22:'PM', 23:'PM'}
	timetype = timetemplate[indate.hour]
	return timetype

def finddaytype(indate, holidaylist):
	weekdaytyp = {0:0, 1:0, 2:0, 3:0, 4:1, 5:2, 6:3}
	datetype = weekdaytyp[indate.weekday()]
	if indate.date() in holidaylist:
		datetype = 3
	return datetype	

def tagesgang(inrentals):
	#Startstunde für idleevent hinzufügen
	for row in inrentals:									
	 	starttimestamp = dateutil.parser.parse(row['STARTED_LOCAL'])
	 	startdate = starttimestamp.date()
		hourcategory = starttimestamp.replace(minute = 0, second = 0, microsecond = 0)
		row['RENTALHRSTART'] = hourcategory
		row['STARTDATE'] = startdate

	RentalsPerHour = collectBy(inrentals, 'RENTALHRSTART', 'DURATION')

	Rentals = {}
	for key,values in RentalsPerHour.iteritems():				#keys and values are iterated
		#print key 												#key is column name identifier
		for x in xrange(0,len(values)):							#all values are iterated while values are collected in List
			values[x] = values[x]								#values are lists of collected Idle Items
		Rentals[key] = len(values)								#define functions to calculate on list

 	summaryfilenames = ['Timestamp','Rentals']
	listeddict = dicttolisteddict(Rentals, summaryfilenames)
	listeddict = sorted(listeddict, key=itemgetter('Timestamp'))
	
	tagesgang = {}
	tagdict = {}
	for hourdict in listeddict:
		if tagesgang.get(hourdict['Timestamp'].date(), True) == True:
			tagdict = {hourdict['Timestamp'].date():[0]*24}
			tagesgang.update(tagdict)

	for key,value in Rentals.iteritems():
		tagesgang[key.date()][key.hour] = value


	exporttagesgang = dicttolisteddict1(tagesgang)	#listmaker for output as table
	#pprint(exporttagesgang)
	return exporttagesgang

def clean(inrentals):
#delete SERVICEDRIVES and invalid DURATION/DISTANCE
	out = []
	for x in inrentals:
		starttimestamp = dateutil.parser.parse(x['STARTED_LOCAL'])
		finishtimestamp = dateutil.parser.parse(x['FINISHED_LOCAL'])
		if x['SERVICEDRIVE'] != '0':
			out.append(x)
		elif int(x['DURATION']) < 60 and int(x['DISTANCE']) < 1:
			out.append(x)
		elif starttimestamp.date() < datetime.date(2013, 11, 1):
			out.append(x)
	for idx in out:
		inrentals.remove(idx)
		
	return inrentals

def yearclean(inrentals):
	#deletes all start and endrental years < 2013 to get rid of 1900'er
	row = 0
	for x in inrentals:
		print(row)
		print inrentals.index(x)
		
		starttimestamp = dateutil.parser.parse(x['STARTED_LOCAL'])
		finishtimestamp = dateutil.parser.parse(x['FINISHED_LOCAL'])
		#print(starttimestamp.date()), ', ', finishtimestamp.date()
		if starttimestamp.date() < datetime.date(2013, 11, 1):
			inrentals.pop(row)
			print "popped start"
		#if finishtimestamp.date() < datetime.date(2013, 11, 1):
		#	inrentals.pop(row)
		#	print "popped end"
		row += 1
	

	#print x
	return inrentals

def dicttolisteddict(inDict, innames):
	outlist = []
	for y in inDict.iteritems():
		listmaker = {'Timestamp':y[0], 'RENTALS':y[1]}
		outlist.append(listmaker)
	return outlist

def dicttolisteddict1(inDict):
	outlist = []
	for y in inDict.iteritems():
		listmaker = {'Date':y[0],'0':y[1][0],'1':y[1][1],'2':y[1][2],'3':y[1][3],'4':y[1][4],'5':y[1][5],'6':y[1][6],'7':y[1][7],'8':y[1][8],'9':y[1][9],'10':y[1][10],'11':y[1][11],'12':y[1][12],'13':y[1][13],'14':y[1][14],'15':y[1][15],'16':y[1][16],'17':y[1][17],'18':y[1][18],'19':y[1][19],'20':y[1][20],'21':y[1][21],'22':y[1][22],'23':y[1][23]}
		outlist.append(listmaker)
	return outlist

def collectBy(inputRows, keyName, valueName):
	results = {}
	for row in inputRows:
		key = row[keyName]
		values = results.get(key, [])
		values.append(row[valueName])
		results[key] = values
	return results

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