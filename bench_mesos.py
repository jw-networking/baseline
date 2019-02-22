#!/bin/python
import requests
import json
import sys
import os

##############################
#vars
##############################
resultsPath="./results"
jsonPath="./mesos"
containerCounts=[5,10,20]
iterations=10
apiURI="http://master1.mesos/v2/apps"
scaleID="scale"
tempID="temp"

##############################
#functions
##############################
def fillTo(appID,count):
	print("fill "+appID+" to "+str(count))

def batchRun(runs):
	print("batch run")
	return "batchrun"

def batchList(runs):
	print("batch list")
	return "batchList"


##############################
#prep
##############################

if(not os.path.isdir(resultsPath)):
	os.mkdir(resultsPath)


##############################
#main test loop
##############################

for count in containerCounts:
	fillTo(scaleID,count)

	print("Starting run test")
	results=open(resultsPath+"/mesos-run-"+str(count)+".raw","w")
	results.write(batchRun(iterations))

	print("Starting list test")
	results=open(resultsPath+"/mesos-list-"+str(count)+".raw","w")
	results.write(batchList(iterations))

##############################
#cleanup
##############################

