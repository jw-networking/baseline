#!/bin/python
import requests
import json
import sys
import os
import re

##############################
#data types
##############################
class service:
	def __init__(self,appID,manifest):
		self.appID=appID
		self.manifest=manifest
	
	def __str__(self):
		return self.appID


##############################
#vars
##############################
resultsPath="./results"
jsonPath="./mesos"
containerCounts=[5,10,20]
iterations=10
apiURI="http://master1.mesos:8080/v2/apps"
scale=service("scale",open(jsonPath+"/scale.json").read().replace("\n",""))
ncBack=service("ncBack",open(jsonPath+"/ncBack.json").read().replace("\n",""))

##############################
#functions
##############################
def fillTo(app,count):
	print("fill "+app.appID+" to "+str(count))

def batchRun(runs,svc):
	print("batch run",svc)
	return "batchrun"

def batchList(runs):
	print("batch list")
	return "batchList"

def deployService(svc):
	print("deploying",svc)
	

def destroyService(svc):
	print("destroying",svc)

##############################
#prep
##############################

if(not os.path.isdir(resultsPath)):
	os.mkdir(resultsPath)

deployService(scale)

##############################
#main test loop
##############################

for count in containerCounts:
	fillTo(scale,count)

	print("Starting run test")
	results=open(resultsPath+"/mesos-run-"+str(count)+".raw","w")
	results.write(batchRun(iterations,ncBack))

	print("Starting list test")
	results=open(resultsPath+"/mesos-list-"+str(count)+".raw","w")
	results.write(batchList(iterations))

##############################
#cleanup
##############################

destroyService(scale)
