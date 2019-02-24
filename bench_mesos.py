#!/bin/python
import requests
import json
import sys
import os
import re
import socket
import time

##############################
#data types
##############################
class service:
	def __init__(self,manifest):
		self.manifest=manifest
		self.appID=json.loads(self.manifest)["id"]
	
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
	if status<200 or status>=300:
		print(response)
		exit(status)
	return response

def getScale(svc):
	resp=httpCheck(requests.get,apiURI+svc.appID)
	return json.loads(resp.text)["app"]["tasksRunning"]

def waitTillScaled(svc,count):
	scale=getScale(svc)
	while scale != count:
		print("running =",scale)
		time.sleep(5)
		scale=getScale(svc)
		
##
#main loop

def fillTo(svc,count):
	print("fill "+svc.appID+" to "+str(count))
	update={}
	update["id"]=svc.appID
	update["instances"]=count
	httpCheck(requests.patch,apiURI+svc.appID,json.dumps(update))
	waitTillScaled(svc,count)

def batchRun(runs):
	print("batch run")
	return "batchrun"

def batchList(runs):
	print("batch list")
	return "batchList"

def deployService(svc):
	print("deploying",svc)
	httpCheck(requests.post,apiURI,svc.manifest)
	waitTillScaled(svc,1)

def destroyService(svc):
	print("destroying",svc)
	httpCheck(requests.delete,apiURI+svc.appID)


##############################
#prep
##############################

if(not os.path.isdir(resultsPath)):
	os.mkdir(resultsPath)

ncBackJSON=json.loads(open(jsonPath+"/ncBack.json").read())
ncBackJSON["cmd"]='echo ""| nc '+getIP()+" "+str(ncPort)
scaleJSON=json.loads(open(jsonPath+"/scale.json").read())

scale=service(json.dumps(scaleJSON))
ncBack=service(json.dumps(ncBackJSON))

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
