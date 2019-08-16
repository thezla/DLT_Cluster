#!/usr/bin/env bash

# Scenario 3, script 2/2:
#   16 miners
#   4 Managers
#   1000 transactions

curl -d '{"number": 1000}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/transactions/generate
sleep 0.5

for i in 5000 5100 5200 5300
do
  for j in 1 2 3 4
  do
    echo Adding miners to cluster on port
    curl -i -X GET http://127.0.0.1:$i/cluster/add_miner
    sleep 0.5
  done
done

for i in 5000 5100 5200 5300
do
  curl -i -X GET http://127.0.0.1:$i/cluster/start
  sleep 1
done