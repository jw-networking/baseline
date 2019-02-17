#!/bin/bash
COUNT=10
SCALE=50
RESULTS="./raw"
TEST_KUBE=0
TEST_DOCKER=0
if [[ "$1" == "kube" ]]; then
  TEST_KUBE=1
else
  TEST_DOCKER=1
fi

# <APISERVERDNS> should be replaced at cluster creation time with the ELB in front of the Kube API servers
PAUSE_IMAGE="gcr.io/google_containers/pause:go"
# The Swarm manager will always start at this IP address
TESTER_IP=$(ip a | egrep 'inet.*eth0$' | awk '{print $2};' | awk -F / '{print $1};')

# General utilities

clearJobs() {
  $(jobs | sed -n 's/^\[\(.*\)\].*$/kill \%\1/p' )
}

batch() {
  for i in $(seq 1 1 $COUNT); do eval $1 $i; done
}

# Docker utilities

dockerList() {
  docker  ps
}

deleteContainer() {
  docker  rm -f $1-$2
}

runContainer() {
  docker  run -d --name $1-$2 alpine sleep 86400
}

DOCKER_SCALE=0
fillDockerTo() {
  TARGET=$1
  if [ "$TARGET" -gt "$DOCKER_SCALE" ]; then 
    echo Scaling Up $DOCKER_SCALE to $TARGET
    for (( i=$DOCKER_SCALE ; i<$TARGET; i++)); do runContainer 'scale' $i; done
  else
    echo Scaling Down $TARGET to $DOCKER_SCALE
    for (( i=(($DOCKER_SCALE-1)) ; i>=$TARGET; i--)); do deleteContainer 'scale' $i; done
  fi
  DOCKER_SCALE=$1
}

# Kubernetes utilities

kubeList() {
  kubectl get po
}

deletePod() {
  kubectl  delete job single-$1
}

getRunningCount() {
  kubectl  get po | sed -n '/Running/p' | wc -l 
}

getPendingCount() {
  kubectl  get po | sed -n '/Pending/p' | wc -l 
}

getTerminatingCount() {
  kubectl  get po | sed -n '/Terminating/p' | wc -l
}

# only stress containers should remain running
joinDispatch() {
  t=$( date +"%s" )
  c=$(getRunningCount)
  while [ $c -ne $1 ]
  do
    echo $c of $1 running
    sleep 5
    c=$(getRunningCount)
  done
  dt=`expr $( date +"%s" ) - $t`
  echo $dt
}

RC_CREATED=0
fillKubernetesTo() {
  if [ $RC_CREATED -eq 0 ]; then
    kubectl  run stresser --image $PAUSE_IMAGE --replicas=$1
    RC_CREATED=1
  else
    kubectl  scale --replicas=$1 rc stresser
  fi
  echo Waiting for pods to start.
  joinDispatch $1
}

# measurement functions

dockerBatchRun() {
  for i in $(seq 1 1 $COUNT); do echo Running $i; { time -p nc -l -p 4444 $TESTER_IP ; } 2>&1 >/dev/null | sed -n '/real/p' | awk '{ print $2 }' & docker  run --name single-$i --entrypoint /bin/sh alpine -c "echo '' | nc $TESTER_IP 4444" 2>&1 >/dev/null & wait ; done
}

kubeBatchRun() {
  for i in $(seq 1 1 $COUNT); do echo Running $i; { time -p nc -l -p 4444 $TESTER_IP ; } 2>&1 >/dev/null | sed -n '/real/p' | awk '{ print $2 }' & kubectl  run single-$i --restart Never --image alpine -- sh -c "echo '' | nc $TESTER_IP 4444" &>/dev/null & wait ; done
}

timedBatch() {
  for (( i=$1 ; i<$2; i++)); do { time -p eval $3 ; } 2>&1 >/dev/null | sed -n '/real/p' | awk '{ print $2 }'; done
}

#formating

scaleToPercent(){
  awk "BEGIN {printf \"%.0f\n\",$SCALE*$1};"
}

################################
# Test Harness
################################

test() {
  if [[ "$TEST_KUBE" -eq 1 ]]; then
    fillKubernetesTo $1
    echo Starting run test
    kubeBatchRun > $RESULTS/kube-run-$1.raw
    echo Starting list test
    timedBatch 1 $COUNT "kubeList" > $RESULTS/kube-list-$1.raw
    echo Clearning up Exited containers
    batch "deletePod"
  else
    fillDockerTo $1
    echo Starting run test
    dockerBatchRun > $RESULTS/swarm-run-$1.raw
    echo Starting list test
    timedBatch 1 $COUNT "dockerList" > $RESULTS/swarm-list-$1.raw
    echo Cleaning up Exited containers
    batch "deleteContainer single"
  fi
}



echo Test at 10% 
test $(scaleToPercent .1)

echo Test at 50% 
test $(scaleToPercent .5)

echo Test at 90% 
test $(scaleToPercent .9)

echo Test at 99% 
test $(scaleToPercent .99)

echo Test at 100% 
test $SCALE
