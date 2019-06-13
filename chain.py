import hashlib
import requests
import json
from datetime import datetime
from time import time
from flask import Flask, jsonify, request

class Chain:
    def __init__(self, *args, **kwargs):
        self.chain = []

        # Create the genesis block
        self.new_genesis_block(previous_hash='1', proof=100, block_transactions=[])


    def new_genesis_block(self, proof, previous_hash, block_transactions):
        if not self.chain:
            block = {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': block_transactions,
                'proof': proof,
                'previous_hash': previous_hash or self.hash(self.chain[-1]),
                'size': 0,   # 2MB max size
            }

            self.chain.append(block)
            return block
    

    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def last_block(self):
        return self.chain[-1]     


    def add_block(self, block, manager_id, manager_address, current_transactions):
        """
        Add a new Block to the Blockchain

        :param block: The block to add
        :return: Block that was added
        """
        if block['index'] == self.last_block()['index']+1:
            self.chain.append(block)
            payload = {
                'chain_height': len(self.chain),
                'transaction_pool_size': len(current_transactions),
                'miner_id': block['node'],
                'manager_id': manager_id,
                'time': str(datetime.now())
            }
            # Send data to logging node
            requests.post(url='http://127.0.0.1:4000/report', json=payload)
            return True
        return False

chain = Chain()
app = Flask(__name__)


@app.route('/append_block', methods=['POST'])
def append_block():
    values = request.get_json()
    required = ['block', 'manager_id', 'manager_address']
    if not all(k in values for k in required):
        return 'Missing values', 400
    chain.add_block(values['block'], values['manager_id'], values['manager_address'], values['current_transactions'])
    return 'Block added to chain', 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': chain.chain}
    return jsonify(response), 200


def main():
    # Start Flask app
    app.run(host='127.0.0.1', port=2000, threaded=False)


if __name__ == "__main__":
    main()