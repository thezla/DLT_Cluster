#!/usr/bin/env bash

# Scenario 1, script 1/2:
#   8 miners
#   2 Managers
#   1000 transactions

function ctrl_c() {
    echo "Terminating processes..."
    pkill -9 python
    echo "Shutting down..."
}

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

pkill -9 python
pipenv run python logger.py &
pipenv run python debugger.py &
pipenv run python chain.py &
sleep 2
pipenv run python manager.py -p 5000 &
sleep 1
pipenv run python manager.py -p 5100