#!/usr/bin/env bash

function ctrl_c() {
    echo "Terminating processes..."
    pkill -9 python
    echo "Shutting down..."
}

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

pkill -9 python
pipenv run python logger.py &
PID1=$!
pipenv run python debugger.py &
PID2=$!
pipenv run python chain.py &
PID3=$!
sleep 2
pipenv run python manager.py -p 5000 &
PID4=$!
sleep 1
pipenv run python manager.py -p 5100 &
PID5=$!
sleep 1
pipenv run python manager.py -p 5200
PID6=$!