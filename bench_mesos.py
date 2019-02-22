#!/bin/python
import requests
import json
import sys

#vars
resultsPath="./results"
jsonPath="./mesos"
containerCounts=[5,10,20]
iterations=100
apiURI="http://master1.mesos/v2/apps"

##############################
#functions
##############################
def fillTo(count):
	print("fill to "+str(count))

def batchRun(runs):
	print("batch run")
	return "batchrun"

def batchList(runs):
	print("batch list")
	return "batchList"

def cleanup():
	fillTo(0)

##############################
#main test loop
##############################

for count in containerCounts:
	fillTo(count)

	print("Starting run test")
	results=open(resultsPath+"/mesos-run-"+str(count)+".raw","w")
	results.write(batchRun(iterations))

	print("Starting list test")
	results=open(resultsPath+"/mesos-list-"+str(count)+".raw","w")
	results.write(batchList(iterations))

cleanup()
