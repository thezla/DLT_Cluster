import requests
from flask import Flask, jsonify, request

import csv
from datetime import datetime

app = Flask(__name__)

timestamp = datetime.now()
timestamp = timestamp.strftime('%Y-%m-%d_%H:%M:%S')
current_file = f'tmp/cluster_logs_{timestamp}.tsv'

with open(current_file, 'a+') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    tsv_writer.writerow(['Miner id', 'Manager id', 'Event', 'Timestamp'])

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json()

    with open(current_file, 'a') as out_file:
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow([data['miner_id'], data['manager_id'], data['event'], data['time']])
    return 'Event logged!', 200


def main():
    app.run(host='0.0.0.0', port=3000, threaded=False)

if __name__ == '__main__':
    main()