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
pipenv run python blockchain.py -p 5000 &
pipenv run python blockchain.py -p 5001 &
pipenv run python blockchain.py -p 5002 &
pipenv run python blockchain.py -p 5003

