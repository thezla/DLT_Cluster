import requests
from flask import Flask, jsonify, request

import csv
from datetime import datetime

app = Flask(__name__)

timestamp = datetime.now()
timestamp = timestamp.strftime('%Y-%m-%d_%H_%M_%S')
current_file = f'tmp/cluster_data_{timestamp}.tsv'

with open(current_file, 'a+') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['Chain Height', 'Transaction pool size', 'Miner id', 'Manager id', 'Timestamp'])

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()

    with open(current_file, 'a') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow([data['chain_height'], data['transaction_pool_size'], data['miner_id'], data['manager_id'], data['time']])
    return 'Data logged!', 200


def main():
    app.run(host='0.0.0.0', port=4000, threaded=False)

if __name__ == '__main__':
    main()