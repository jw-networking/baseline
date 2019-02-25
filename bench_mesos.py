#!/bin/python
import requests
import json
import sys
import os
import re
import socket
import time
from threading import Thread

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
		raise LookupError(response)
	return response

def getScale(svc):
	try:
		resp=httpCheck(requests.get,apiURI+svc.appID)
	except LookupError as err:
		raise 
	
	return json.loads(resp.text)["app"]["tasksRunning"]

def waitTillScaled(svc,count):
	running=None
	while running != count:
		try:
			running=getScale(svc)
		except LookupError:
			running=0
		time.sleep(5)
		running=getScale(svc)
		
##
#main loop

def fillTo(svc,count):
	print("fill "+svc.appID+" to "+str(count))
	update={}
	update["id"]=svc.appID
	update["instances"]=count
	httpCheck(requests.patch,apiURI+svc.appID,json.dumps(update))
	waitTillScaled(svc,count)

def batchRun(runs,rawFD,avgFD):
	raw=""
	total=0
	avg=0
	timeStart=[None]
	timeStop=[None]

	def socList():
		try:
			listen=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			listen.bind((getIP(),ncPort))
			listen.listen(1)
		except:
			print("can't open socket")
			exit(2)
		con,addr=listen.accept()
		timeStop[0]=time.time()
		con.close()

	def startNcBack():
		try:
			destroyService(ncBack)
			waitTillScaled(ncBack,0)
		except LookupError:
			pass
		timeStart[0]=time.time()
		deployService(ncBack)

	for i in range(runs):
		print("run "+str(i)+" of "+str(runs))
		socListThread=Thread(target=socList)
		startNcBackThread=Thread(target=startNcBack)

		socListThread.start()

		startNcBackThread.start()

		if socListThread.isAlive():
			socListThread.join()
		diff=timeStop[0]-timeStart[0]
		total+=diff
		raw+=str(diff)+"\n"
	rawFD.write(raw)
	avgFD.write(str(total/runs)+"\n")
	



def batchList(runs,rawFD,avgFD):
	raw=""
	total=0
	avg=0
	timeStart=0.0
	timeStop=0.0
	for i in range(runs):
		timeStart=time.time()
		httpCheck(requests.get,apiURI)
		timeStop=time.time()
		diff=timeStop-timeStart
		total+=diff
		raw+=str(diff)+"\n"
	rawFD.write(raw)
	avgFD.write(str(total/runs)+"\n")

def deployService(svc):
	try:
		httpCheck(requests.post,apiURI,svc.manifest)
	except LookupError:
		raise

def destroyService(svc):
	try:
		httpCheck(requests.delete,apiURI+svc.appID)
	except LookupError:
		raise

##############################
#prep
##############################

if(not os.path.isdir(resultsPath)):
	os.mkdir(resultsPath)

ncBackJSON=json.loads(open(jsonPath+"/ncBack.json").read())
ncBackJSON["cmd"]='echo "" | nc '+getIP()+" "+str(ncPort)
scaleJSON=json.loads(open(jsonPath+"/scale.json").read())

scale=service(json.dumps(scaleJSON))
ncBack=service(json.dumps(ncBackJSON))

print("deploying", scale.appID)
deployService(scale)
waitTillScaled(scale,1)

##############################
#main test loop
##############################

for count in containerCounts:
	fillTo(scale,count)

	print("Starting run test")
	resultsRaw=open(resultsPath+"/mesos-run-"+str(count)+".raw","w")
	resultsAvg=open(resultsPath+"/mesos-run-"+str(count)+".avg","w")
	batchRun(iterations,resultsRaw,resultsAvg)

	print("Starting list test")
	resultsRaw=open(resultsPath+"/mesos-list-"+str(count)+".raw","w")
	resultsAvg=open(resultsPath+"/mesos-list-"+str(count)+".avg","w")
	batchList(iterations,resultsRaw,resultsAvg)

##############################
#cleanup
##############################

print("destroying "+scale.appID+" & "+ncBack.appID)
try:
	destroyService(scale)
except LookupError:
	pass
try:
	destroyService(ncBack)
except LookupError:
	pass
