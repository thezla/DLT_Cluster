import hashlib
from datetime import date, datetime
import json
from uuid import uuid4
from time import sleep
from urllib.parse import urlparse
import random
from threading import Thread

import requests
from flask import Flask, jsonify, request

class Miner:
    def __init__(self):
        self.manager_node = ''
        self.node_identifier = str(uuid4()).replace('-', '')
        self.node_address = ''
        self.current_transactions = []
        self.last_block = {}
        self.interval = 1
        self.start_value = 0

        # Activates / Deactivates mining process
        self.is_mining = False

    def new_block(self, proof, previous_hash, block_transactions, node_identifier, last_block):
        """
        Create a new Block for the manager node

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """
        block_size = 0
        for t in block_transactions:
            block_size += t['size']

        block = {
            'index': last_block['index'] + 1,
            'timestamp': datetime.now().isoformat(),
            'transactions': block_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
            'size': block_size,   # 2MB max size
            'node': node_identifier,
        }
        return block
        
    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        :return <sha256 hash>
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

        proof = self.start_value
        while self.is_mining:
            if self.valid_proof(last_proof, proof, last_hash):
                return proof
            else:
                proof += self.interval
            #sleep(random.randint(1,4))
        return -1

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
        return guess_hash[:5] == "00000"         # Hash made easy to simulate mining
    
    def set_address(self, address):
        self.node_address = address
    
    def set_manager_address(self, address):
        self.manager_node = address
    
    def get_node_id(self):
        return self.node_identifier
    
    def generate_log(self, event):
        payload = {
            'miner_id': self.node_address,
            'manager_id': self.manager_node,
            'event': event,
            'time': str(datetime.now())
        }
        # Send data to logging node
        requests.post(url='http://127.0.0.1:3000/report', json=payload)

# Instantiate the Node
app = Flask(__name__)
miner = Miner()


class Mine(Thread):
    def __init__(self, task_id):
        Thread.__init__(self)
        self.task_id = task_id
        self.completed = False

    def run(self):
        '''
        Starts mining process

        :param manager_node <string> Manager node of miner
        :return <bool> True if managed to mine block and it was included in the chain, False if not
        '''
        # Compose list of transactions of block
        block_transactions = miner.current_transactions
        if block_transactions:
            last_block = miner.last_block
            # Enter proof_of_work loop to find proof with algorithm
            proof = miner.proof_of_work(last_block)
            if proof > -1:
                # Forge the new Block by adding it to the chain
                previous_hash = miner.hash(last_block)
                block = miner.new_block(proof, previous_hash, block_transactions, miner.node_identifier, last_block)
                if block != None:
                    # We must receive a reward for finding the proof.
                    # The sender is "0" to signify that this node has mined a new coin.
                    payload = {
                        'sender': '0',
                        'recipient': miner.node_identifier,
                        'amount': 1
                    }
                    miner.generate_log('Miner found block')
                    r = requests.post(url=f'http://{miner.manager_node}/slave/done', json=block)
                    if r.status_code == requests.codes.ok:
                        #requests.post(url=f'http://{miner.manager_node}/transactions/new', json=payload)   # Reward miner for block
                        self.completed = True
                        


        miner.current_transactions = []
        miner.last_block = dict()

    def join(self):
        Thread.join(self)
        return self.completed


@app.route('/start', methods=['POST'])
def start_mining():
    miner.generate_log('Started mining')
    miner.is_mining = True
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['transactions', 'last_block', 'interval']
    if not all(k in values for k in required):
        return 'Missing values', 400

    if values != None:
        miner.current_transactions = values['transactions']
        miner.last_block = values['last_block']
        miner.interval = values['interval']
        miner.start_value = values['start_value']

        # If block was mined correctly
        async_task = Mine(task_id=1)
        async_task.setName('Mine proof')
        async_task.start()
        #completed = async_task.join()
        '''if completed:
            response = {'message': 'Block found, stopped mining'}
        else:
            response = {'message': 'Block not found, stopped mining'}
        return jsonify(response), 200'''
        return 'Mining completed', 200

    miner.current_transactions = []
    miner.last_block = dict()
    #return jsonify({'message': 'Transaction list was None, stopped mining'}), 400


@app.route('/stop', methods=['GET'])
def stop_mining():
    miner.generate_log('Stopped mining')
    miner.is_mining = False
    return f'Mining process stoppped in node: {miner.node_address}', 200


@app.route('/transactions', methods=['GET'])
def get_transactions():
    response = {
        'transactions': miner.current_transactions,
        'size': len(miner.current_transactions)
    }
    return jsonify(response), 200


@app.route('/mining', methods=['GET'])
def mining():
    return str(miner.is_mining), 200

'''
@app.route('/set_manager_address', methods=['POST'])
def set_manager():
    manager_address = request.get_json()
    miner.manager_node = manager_address
    return f'Manager node address set to {manager_address}', 200


@app.route('/set_address', methods=['POST'])
def set_address():
    node_address = request.get_json()
    miner.node_address = node_address
    return f'Node address set to {node_address}', 200
'''

@app.route('/address', methods=['GET'])
def get_address():
    return f'Self: {miner.node_address}, Manager: {miner.manager_node}', 200


# Starts a miner node
def start(address, port, manager_address):
    miner.set_address(f'{address}:{port}')
    miner.set_manager_address(f'{manager_address}')
    miner.generate_log('Miner created')

    # Start flask app
    app.run(host='127.0.0.1', port=port, threaded=True)