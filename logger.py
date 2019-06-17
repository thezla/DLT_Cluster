import requests
from flask import Flask, jsonify, request

import csv
from datetime import datetime

app = Flask(__name__)

history_new = []
history_old = []

timestamp = datetime.now()
timestamp = timestamp.strftime('%Y-%m-%d_%H_%M_%S')
current_file = f'tmp/cluster_data_{timestamp}.tsv'
current_file_old = f'tmp_old/cluster_data_{timestamp}.tsv'

with open(current_file, 'a+') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['Chain Height', 'Transaction pool size', 'Miner id', 'Manager id', 'Timestamp'])

with open(current_file_old, 'a+') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['Chain Height', 'Transactions done', 'Miner id', 'Timestamp'])

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()

    with open(current_file, 'a') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow([data['chain_height'], data['transaction_pool_size'], data['miner_id'], data['manager_id'], data['time']])
    return 'Data logged!', 200


@app.route('/report_old', methods=['POST'])
def report_old():
    data = request.get_json()

    with open(current_file_old, 'a') as out_file:
        if data not in history_old:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow([data['chain_height'], data['transactions_done'], data['miner_id'], data['time']])
            history_old.append(data)
    return 'Data logged!', 200

def main():
    app.run(host='127.0.0.1', port=4000, threaded=True)

if __name__ == '__main__':
    main()