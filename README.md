
## Clustering Distributed Ledger Technologies for Scalability.

In this project we have added on top of the base blockchain code fork found below.
The goal of this project is to study how clustering of DLT nodes affects scalability.
* Manager nodes are in charge of clusters of miner nodes. 
* The miner nodes are not aware of the blockchain and only follow the instructions of the manager node.
* The manager nodes form a network with each other and keep their chains and transaction pool synced.
* The manager nodes compete to mine blocks, but the miner nodes in each cluster work together to find the proof.

Forked from [Building a Blockchain](https://github.com/dvf/blockchain). 

## Installation

1. Make sure [Python 3.7+](https://www.python.org/downloads/) is installed.
2. Install [pipenv](https://github.com/kennethreitz/pipenv). 

```
$ pip install pipenv 
```
3. Install requirements  
```
$ pipenv install 
``` 

4. Run a simple blockchain:
    * `$ pipenv run python blockchain.py` 
    * `$ pipenv run python blockchain.py -p 5001`, where -p is the port, default IP is 0.0.0.0
    * `$ pipenv run python blockchain.py --port 5002`

5. Run a cluster of miners:
    * Start a manager node: `$ pipenv run manager.py -p 5000`, where -p is the port, default IP is 0.0.0.0
    * To start a slave node you have to send a HTTP/GET request to the manager node's endpoint, e.g. "http://0.0.0.0:5000/cluster/add_miner". We would recommend the application PostMan for sending requests. You can also use a browser.

## TODO

* Syncing of transactions between clusters

* Make the program exit cleaner when CTRL-C is pressed.

~~* Make miner nodes cooperate to find proof.~~

~~* Make it so the transactions are not removed from the pool while composed into blocks. Only when a block has been mined.~~

~~* Change the transaction pool from a list to a dictionary to allow faster lookups and deletions.~~

