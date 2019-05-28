import hashlib
import json
from time import time
from time import sleep
from urllib.parse import urlparse
from uuid import uuid4
import random
from threading import Thread
from datetime import datetime
import subprocess
import miner
import importlib
import os
from pathlib import Path

import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.current_transactions = dict()
        self.chain = []
        self.nodes = set()
        self.slave_nodes = set()
        self.address = ''
        self.cluster_start_port = 0

        # Create the genesis block
        self.new_genesis_block(previous_hash='1', proof=100, block_transactions=[])

        # Add first neighbor node
        self.register_node("http://0.0.0.0:5000")

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)

            #self.address = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
            #self.address = parsed_url.path
        else:
            raise ValueError('Invalid URL')


    def resolve_nodes(self, node_address):
        """
        Spread node list to neighbor nodes
        """
        # TODO: Ability to remove adress completely from network
        neighbors = self.nodes
        if len(neighbors) > 1:
            payload = {'nodes': list(neighbors)}
            headers = {'content-type': 'application/json'}
            for node in neighbors:
                # Do not request node list from itself
                if node != self.address:
                    requests.post(url=f'http://{node}/nodes/register', json=payload, headers=headers)


    def valid_chain(self, chain):
        """
        Determine if a given manager is valid

        :param chain: A manager
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            # TODO: FIX!!!!!!!!!
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            if node != self.address:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == requests.codes.ok:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length >= max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True
        return False

    def compose_block_transactions(self):
        # Max size of block in "kilobytes"
        max_size = 2000
        block_size = 0
        block_transactions = []

        for identifier, transaction in self.current_transactions.items():
            transaction_size = transaction['size']
            if (transaction_size + block_size) > max_size:
                return block_transactions
            else:
                if transaction:
                    block_transactions.append(transaction)
                block_size += transaction_size
        return block_transactions

    def add_block(self, block):
        """
        Add a new Block to the Blockchain

        :param block: The block to add
        :return: Block that was added
        """
        # Ensure we are the longest chain
        self.resolve_conflicts()
        self.chain.append(block)
        for transaction in block['transactions']:
            if transaction['id'] in self.current_transactions:
                self.current_transactions.pop(transaction['id'])
        
        # Construct log entry
        payload = {
            'chain_height': len(self.chain),
            'transaction_pool_size': len(self.current_transactions),
            'miner_id': block['node'],
            'manager_id': node_identifier,
            'time': str(datetime.now())
        }
        # Send data to logging node
        requests.post(url='http://0.0.0.0:4000/report', json=payload)
        return block

    def new_genesis_block(self, proof, previous_hash, block_transactions):
        if not self.chain:
            block_size = 0
            for t in block_transactions:
                block_size += t['size']

            block = {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': block_transactions,
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.chain[-1]),
                'size': block_size,   # 2MB max size
            }

            self.chain.append(block)
            return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        transaction_id = str(uuid4()).replace('-', '')
        self.current_transactions[transaction_id] = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'size': random.randint(10,100),         # Simulated size in kilobytes
            'id': transaction_id                    # Unique ID
        }
        return len(self.chain)+1


    # TODO: Fixa transaktionssync
    def sync_transactions(self):
        if len(self.nodes) > 1:
            for node in self.nodes:
                requests.post(url=f'http://{node}/transactions/update', json=self.current_transactions)


    #@property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    '''def start_mining(self):
        payload = {
            'transactions': self.compose_block_transactions(),
            'last_block': self.last_block()
        }
        for node in self.slave_nodes:
            requests.post(url='http://'+node+'/start', json=payload)'''
    
    def set_address(self, address):
        parsed_url = urlparse(address)
        
        if parsed_url.netloc:
            self.address = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.address = parsed_url.path
    
    def set_cluster_start_port(self, n):
        self.cluster_start_port = n

    def get_cluster_start_port(self):
        return self.cluster_start_port
    
    def stop_all_clusters(self):
        if len(self.nodes) > 1:
            for node in self.nodes:
                if node is not self.address:
                    requests.get(url=f'http://{node}/cluster/stop')

    
    def start_all_clusters(self):
        if len(self.nodes) > 1:
            for node in self.nodes:
                if node is not self.address:
                    requests.get(url=f'http://{node}/cluster/start')


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique id for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
manager = Blockchain()

# Activates / Deactivates node list syncing process
is_syncing = True

# For filtering of requests from miners
block_found = False
waiting_for_response = False
cluster_running = False


class Manage(Thread):
    def __init__(self, task_id):
        Thread.__init__(self)
        self.task_id = task_id
    
    # TODO: Sometimes, manager object == None, don't know why
    def run(self):
        global waiting_for_response
        global block_found
        global cluster_running

        while True:
            if cluster_running and manager.current_transactions:
                if not waiting_for_response and not block_found:
                    
                    transactions = manager.compose_block_transactions()
                    if not transactions:
                        sleep(0.1)
                        continue
                    last_block = manager.last_block()
                    interval = len(manager.slave_nodes)
                    start_value = 0

                    for node in manager.slave_nodes:
                        payload = {
                            'transactions': transactions,
                            'last_block': last_block,
                            'interval': interval,
                            'start_value': start_value
                        }

                        requests.post(url='http://'+node+'/start', json=payload)
                        start_value+=1
                    waiting_for_response = True
                # Miners are done, start on another block
                elif block_found:
                    waiting_for_response = False
                    block_found = False
            else:
                sleep(0.1)


class NewMiner(Thread):
    def __init__(self, task_id):
        Thread.__init__(self)
        self.task_id = task_id
    
    def run(self):
        #port = 6000+len(manager.slave_nodes)+len(manager.nodes)*100
        port = manager.get_cluster_start_port()+len(manager.slave_nodes)
        address = f'0.0.0.0:{port}'
        manager.slave_nodes.add(address)
        #man_address = manager.address

        import sys
        import importlib.util

        # Create an instance of the miner.py module
        SPEC_OS = importlib.util.find_spec('miner')
        new_miner = importlib.util.module_from_spec(SPEC_OS)
        SPEC_OS.loader.exec_module(new_miner)
        sys.modules[f'miner_{address}'] = new_miner

        new_miner.start(address='http://0.0.0.0', port=port, manager_address=manager.address)


class Sync(Thread):
    def __init__(self, task_id):
        Thread.__init__(self)
        self.task_id = task_id

    def run(self):
        while True:
            if is_syncing:
                manager.resolve_nodes(manager.address)
                sleep(5)


@app.route('/sync', methods=['GET'])
def sync_nodes():
    global is_syncing
    is_syncing = True
    async_task = Sync(task_id=2)
    async_task.setName('Syncing node lists')
    try:
        with app.test_request_context():
            async_task.start()
        return 'Started syncing node lists', 200
    except RuntimeError:
        return 'Node is already syncing', 400


@app.route('/sync/stop', methods=['GET'])
def stop_syncing():
    global is_syncing
    is_syncing = False
    return 'Syncing process stopped', 400


@app.route('/transactions/new', methods=['POST'])
def add_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = manager.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 200


@app.route('/transactions', methods=['GET'])
def get_transactions():
    response = {
        'transactions': manager.current_transactions,
        'size': len(manager.current_transactions)
    }
    return jsonify(response), 200


@app.route('/slave/done', methods=['POST'])
def slave_done():
    global block_found
    if not block_found:     # Ignore all requests except first one
        stop_cluster()
        block_found = True
        block = request.get_json()
        manager.add_block(block)
        manager.stop_all_clusters()
        manager.sync_transactions()
        start_cluster()
        manager.start_all_clusters()
        return 'Block recieved, restarting mining', 200
    return 'Block already found, restarting mining', 400


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': manager.chain,
        'length': len(manager.chain),
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(manager.nodes)
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values['nodes']
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        manager.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(manager.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = manager.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': manager.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': manager.chain
        }
    return jsonify(response), 200


@app.route('/cluster', methods=['GET'])
def get_cluster():
    return jsonify(list(manager.slave_nodes)), 200


# Adds a miner node to cluster
@app.route('/cluster/add_miner', methods=['GET'])
def add_miner():
    async_task = NewMiner(task_id=3)
    async_task.setName(f'New Miner: 0.0.0.0:{manager.get_cluster_start_port()}')
    try:
        with app.test_request_context():
            async_task.start()
    except RuntimeError:
        return 'Could not create a new miner', 400

    return 'Miner node created and added to cluster!', 200



# Tells cluster to start mining
@app.route('/cluster/start', methods=['GET'])
def start_cluster():
    global cluster_running
    #global block_found

    if not cluster_running:
        if manager.slave_nodes:
            cluster_running = True
            return 'Cluster mining initiated!', 200
        return 'Error: No nodes in cluster', 400
    return 'Error: Cluster is already running', 400


# Tells cluster to stop mining
@app.route('/cluster/stop', methods=['GET'])
def stop_cluster():
    global cluster_running
    cluster_running = False
    for node in manager.slave_nodes:
        r = requests.get(f'http://{node}/stop')
        if not r.status_code == requests.codes.ok:
            return f'Failed to deactivate miner {node} in cluster', 400
    return 'Cluster mining deactivated!', 200


# Generate transactions for testing
@app.route('/transactions/generate', methods=['POST'])
def generate_transactions():
    values = request.get_json()
    number = values.get('number')

    for i in range(0, number):
        amount = random.randint(1,1000)
        sender = random.randint(1,100)
        recipient = random.randint(1,100)
        while recipient == sender:
            recipient = random.randint(1,100)
        
        manager.new_transaction(sender, recipient, amount)
    return f'{number} transactions generated!'


@app.route('/transactions/update', methods=['POST'])
def update_transactions(self):
    new_transactions = request.get_json()
    self.current_transactions = new_transactions
    return 'Transactions updated!', 200


@app.route('/address', methods=['GET'])
def get_address():
    return f'{manager.address}', 200


# Initialization --------------------
# Activate syncing of manager node list
sync_nodes()
manager.set_cluster_start_port(6000+(len(manager.nodes)*100))
# Get longest blockchain
#manager.resolve_conflicts()

# Activate manage thread
manage_task = Manage(task_id=4)
manage_task.setName('Manage Miners')
with app.test_request_context():
    manage_task.start()


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    # Add own address to node list
    address = f'http://0.0.0.0:{port}'
    manager.set_address(address)
    manager.register_node(address)

    # Prevent address collisions when using the local network, change this in bigger networks
    manager.set_cluster_start_port(6000+(len(manager.nodes)*100))

    # Start Flask app
    app.run(host='0.0.0.0', port=port, threaded=False)

if __name__ == '__main__':
    main()