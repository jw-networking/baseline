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
		print(response)
		exit(status)
	return response

def getScale(svc):
	resp=httpCheck(requests.get,apiURI+svc.appID)
	return json.loads(resp.text)["app"]["tasksRunning"]

def waitTillScaled(svc,count):
	scale=None
	while scale != count:
		try:
			scale=getscale(svc):
		except:
			count=0
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

def batchRun(runs,rawFD,avgFD):
	raw=""
	total=0
	avg=0
	timeStart=0.0
	timeStop=0.0

	def socList():
		listen=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		listen.bind((getIP(),ncPort))
		listen.listen(1)
		con,addr=listen.accept()
		con.close()



	def startNcBack():
		deployService(ncBack)
		waitTillScaled(ncBack,1)


	for i in range(runs):
		socListThread=Thread(target=socList)
		startNcBack=Thread(target=startNcBack)

		socListThread.start()

		timeStart=time.time()
		startNcBack.start()

		if socListThread.isAlive():
			socListThread.join()
		timeStop=time.time

		if startNcBack.isAlive():
			startNcBack.join()
		destroyService(ncBack)
		waitTillScaled(ncBack,0)



def batchList(runs,rawFD,avgFD):
	raw=""
	total=0
	avg=0
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
	httpCheck(requests.post,apiURI,svc.manifest)

def destroyService(svc):
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

print("deploying",scale.appID)
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

print("destroying",svc)
destroyService(scale)
