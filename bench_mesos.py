#!/bin/python
import requests
import json
import sys
import os
import re
import socket

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
ncPort=4444
scale=None
ncBack=None

##############################
#functions
##############################

##
#services
def getIP():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	IP=s.getsockname()[0]
	s.close()
	
	return IP

def httpCheck(cmd,destination,json=None):
	response=cmd(destination,data=json)
	status=response.status_code
	if status<200 or status>300:
		print(response)
		exit(status)
	return response
	

##
#main loop

def fillTo(app,count):
	print("fill "+app.appID+" to "+str(count))

def batchRun(runs):
	print("batch run")
	return "batchrun"

def batchList(runs):
	print("batch list")
	return "batchList"

def deployService(svc):
	print("deploying",svc)
	httpCheck(requests.post,apiURI,svc.manifest)

def destroyService(svc):
	print("destroying",svc)


##############################
#prep
##############################

if(not os.path.isdir(resultsPath)):
	os.mkdir(resultsPath)

ncBackJSON=json.loads(open(jsonPath+"/ncBack.json").read())
ncBackJSON["cmd"]='echo ""| nc '+getIP()+" "+str(ncPort)
scaleJSON=json.loads(open(jsonPath+"/scale.json").read())

scale=service("scale",json.dumps(scaleJSON))
ncBack=service("ncBack",json.dumps(ncBackJSON))

deployService(scale)

##############################
#main test loop
##############################

for count in containerCounts:
	fillTo(scale,count)

	print("Starting run test")
	results=open(resultsPath+"/mesos-run-"+str(count)+".raw","w")
	results.write(batchRun(iterations))

	print("Starting list test")
	results=open(resultsPath+"/mesos-list-"+str(count)+".raw","w")
	results.write(batchList(iterations))

##############################
#cleanup
##############################

destroyService(scale)
