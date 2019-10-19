import requests
from flask import Flask, jsonify, request

import csv
from datetime import datetime

app = Flask(__name__)

history_new = []
history_old = []

timestamp = datetime.now()
timestamp = timestamp.strftime('%Y-%m-%d_%H_%M_%S')
current_file = f'../tmp/cluster_data_{timestamp}.tsv'
current_file_old = f'../tmp_old/cluster_data_{timestamp}.tsv'
traffic = 0

with open(current_file, 'a+') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['Chain Height', 'Transaction pool size', 'Miner id', 'Manager id', 'Traffic count', 'Timestamp'])

with open(current_file_old, 'a+') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['Chain Height', 'Transactions done', 'Miner id', 'Traffic count', 'Timestamp'])

@app.route('/report', methods=['POST'])
def report():
    global traffic
    data = request.get_json()

    with open(current_file, 'a') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow([data['chain_height'], data['transaction_pool_size'], data['miner_id'], data['manager_id'], traffic, data['time']])
    return 'Data logged!', 200


@app.route('/report_old', methods=['POST'])
def report_old():
    global traffic
    data = request.get_json()

    with open(current_file_old, 'a') as out_file:
        if data not in history_old:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow([data['chain_height'], data['transaction_pool_size'], data['miner_id'], traffic, data['time']])
            history_old.append(data)
    return 'Data logged!', 200

@app.route('/report_traffic', methods=['GET'])
def report_traffic():
    global traffic
    traffic += 1
    return 'Traffic recorded!', 200

def main():
    app.run(host='127.0.0.1', port=4000, threaded=True)

if __name__ == '__main__':
    main()