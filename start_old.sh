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
pipenv run python debugger.py &
sleep 1
pipenv run python chain.py &
sleep 1
pipenv run python blockchain.py -p 5000 &
sleep 1
pipenv run python blockchain.py -p 5001 &
sleep 1
pipenv run python blockchain.py -p 5002 &
sleep 1
pipenv run python blockchain.py -p 5003 &
sleep 2
curl -d '{"number": 1000}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/transactions/generate
sleep 0.5
curl -d '{"number": 1000}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5001/transactions/generate
sleep 0.5
curl -d '{"number": 1000}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5002/transactions/generate
sleep 0.5
curl -d '{"number": 1000}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5003/transactions/generate