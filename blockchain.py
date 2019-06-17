import hashlib
import json
from time import time
from time import sleep
from urllib.parse import urlparse
from uuid import uuid4
import random
import threading
import datetime

import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_genesis_block(previous_hash='1', proof=100, block_transactions=[])

        # Add first neighbor node
        self.register_node("http://127.0.0.1:5000")

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
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
                if node != node_address:
                    response = requests.post(url=f'http://{node}/nodes/register', json=payload, headers=headers)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            #print(f'{last_block}')
            #print(f'{block}')
            #print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
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
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
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
        if self.chain:
            while True:
                if self.current_transactions:
                    transaction_size = self.current_transactions[0]['size']
                    if (transaction_size + block_size) <= max_size:
                        block_transactions.append(self.current_transactions[0])
                        del self.current_transactions[0]
                        block_size += transaction_size
                    else:
                        break
                else:
                    # Put transactions back in front of queue
                    for e in reversed(block_transactions):
                        self.current_transactions.insert(0, e)
                    return []
        return block_transactions

    def new_block(self, proof, previous_hash, block_transactions, node_identifier):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        # Ensure we are the longest chain
        self.resolve_conflicts()
        block_size = 0
        for t in block_transactions:
            block_size += t['size']

        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'transactions': block_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'size': block_size,   # 2MB max size
            'node': node_identifier
        }

        self.chain.append(block)
        print(block['node'])

        # Send confirmed block to logger (3 blocks ago)
        if len(self.chain) > 4:
            transactions = 0
            for b in self.chain:
                transactions += len(b['transactions'])
                if b['index'] == len(self.chain)-3:
                    #transactions_left = len(self.current_transactions) + len(self.chain[b['index']+1]['transactions']) + len(self.chain[b['index']+2]['transactions']) + len(self.chain[b['index']+3]['transactions'])
                    payload = {
                        'chain_height': b['index'],
                        'transactions_done': transactions,
                        'miner_id': b['node'],
                        'time': b['timestamp']
                    }
                    # Send data to logging node
                    requests.post(url='http://127.0.0.1:4000/report_old', json=payload)
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
                'node': node_identifier
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
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'size': random.randint(10,100),         # Simulated size in kilobytes
            'id': str(uuid4()).replace('-', '')     # Unique ID
        })

        return self.last_block['index'] + 1
    
    # TODO: Fixa transaktionssync
    def resolve_transactions():
        pass


    @property
    def last_block(self):
        if self.chain:
            return self.chain[-1]
        return 0

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = random.randint(0, 100000)
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        # Simulated mining
        #sleep(random.randint(1,4))
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:5] == "00000"           # Hash made easy to simulate mining
    


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
node_address = ""

# Instantiate the Blockchain
blockchain = Blockchain()

# Activates / Deactivates mining process
is_mining = False

# Activates / Deactivates node list syncing process
is_syncing = True

# Asynchronous mining
class Mine(threading.Thread):
    def __init__(self, task_id):
        threading.Thread.__init__(self)
        self.task_id = task_id

    def run(self):
        while is_mining:
            #TODO: Sync transactions across network

            # Compose list of transactions of block
            block_transactions = blockchain.compose_block_transactions()
            if block_transactions:
                # We run the proof of work algorithm to get the next proof...
                last_block = blockchain.last_block
                proof = blockchain.proof_of_work(last_block)

                # Forge the new Block by adding it to the chain
                previous_hash = blockchain.hash(last_block)
                block = blockchain.new_block(proof, previous_hash, block_transactions, node_identifier)
                if block != None:
                    response = {
                        'message': "New Block Forged",
                        'index': block['index'],
                        'transactions': block['transactions'],
                        'proof': block['proof'],
                        'previous_hash': block['previous_hash'],
                        'size': block['size']
                    }

                    # We must receive a reward for finding the proof.
                    # The sender is "0" to signify that this node has mined a new coin.
                    blockchain.new_transaction(
                        sender="0",
                        recipient=node_identifier,
                        amount=1,
                    )

class Sync(threading.Thread):
    def __init__(self, task_id):
        threading.Thread.__init__(self)
        self.task_id = task_id

    def run(self):
        while is_syncing:
            blockchain.resolve_nodes(node_address)
            sleep(8)


@app.route('/mine', methods=['GET'])
def mine():
    global is_mining
    is_mining = True
    async_task = Mine(task_id=1)
    try:
        with app.test_request_context():
            async_task.start()
        return 'Started mining process', 200
    except RuntimeError:
        return 'Node is already mining', 400


@app.route('/mine/stop', methods=['GET'])
def stop_mining():
    global is_mining
    is_mining = False
    return 'Mining process stopped', 400


@app.route('/sync', methods=['GET'])
def sync_nodes():
    global is_syncing
    is_syncing = True
    async_task = Sync(task_id=2)
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
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/transactions', methods=['GET'])
def get_transactions():
    response = {
        'transactions': blockchain.current_transactions,
        'size': len(blockchain.current_transactions)
    }
    return jsonify(response), 200


@app.route('/transactions/sync', methods=['POST'])
def sync_transactions(self):
    values = request.get_json()

    transactions = values['transactions']
    if transactions is None:
        return "Error: Please supply a valid list of transactions", 400

    for trans in transactions:
        if trans not in self.current_transactions:      #TODO: Bättre datastruktur, hashmap?
            blockchain.new_transaction()

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values['nodes']
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


# Generate transactions for testing
@app.route('/transactions/generate', methods=['POST'])
def generate_transactions():
    values = request.get_json()
    number = values.get('number')

    for i in range(0, number):
        amount = recipient = random.randint(1,1000)
        sender = random.randint(1,100)
        recipient = random.randint(1,100)
        while recipient == sender:
            recipient = random.randint(1,100)
        
        blockchain.new_transaction(sender, recipient, amount)
    return '{amount} transactions generated!'

# Initialization --------------------
# Activate syncing of node lists
sync_nodes()

# Activate mining
mine()

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    # Add own address to node list
    address = 'http://127.0.0.1:{}'.format(port)
    blockchain.register_node(address)
    node_address = address

    # Start flask app
    app.run(host='127.0.0.1', port=port, threaded=False)