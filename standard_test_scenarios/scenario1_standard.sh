#!/usr/bin/env bash

function ctrl_c() {
    echo "Terminating processes..."
    pkill -9 python
    echo "Shutting down..."
}

# trap ctrl-c and call ctrl_c()
trap ctrl_c INT

pkill -9 python
pipenv run python ../logger.py &
pipenv run python ../debugger.py &
sleep 1
pipenv run python ../chain.py &

for i in 5000 5001 5002 5003 5004 5005 5006 5007
do
  echo Adding nodes to network on port $i
  pipenv run python ../blockchain.py -p $i &
  sleep 1
done

#curl -d '{"number": 1000}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/transactions/generate