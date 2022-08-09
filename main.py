from ast import Global
import threading
import socket
from utility import synchronized
from collections import deque
import json
import requests
import pickle
# Gateway

host = '127.0.0.1'
port = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

# transaction api
API_TRANSACTION = ["http://127.0.0.1:8000/"]

# queue for transactions [transaction, data] : first index first out
queue = []


def find_free_api():
    """
    load balancing
    """
    status = {}
    free = {}
    for api in API_TRANSACTION:
        res = requests.get(url=api)
        data = res.json()
        status[api] = data['count']

    for api, count in status.items():
        if free == {} or free['count'] < count:
            free['count'] = count
            free['api'] = api

    return free['api']


@synchronized
def handel(transaction, client):
    """handel sending transaction to servers"""
    API = find_free_api()

    try:
        res = requests.get(url=API, data=transaction, timeout=15)
        data = res.json()
        client.send(pickle.dumps(data))
        client.close()

    except requests.Timeout:
        client.send(pickle.dumps({'msg': 'timeout'}))
        client.close()

    from connect import table
    table.insert(
        pk=transaction["pk"],
        content=transaction["content"]
    )


def get_transaction_from_queue(transaction_id: int) -> list or None:
    for transaction, client in queue:
        pk = transaction.get('pk')
        if pk == transaction_id:
            return [transaction, client]
        return None


def receive():
    global queue
    while True:
        client, address = server.accept()

        request = client.recv(1024)
        data = pickle.loads(request)

        # check pk most be in transaction data
        if 'pk' not in data:
            client.send(pickle.dumps({'msg': 'pk is required'}))
            client.close()
            continue

        pk = data['pk']

        from_queue = get_transaction_from_queue(pk)
        if from_queue is not None:

            # remove transaction from queue when receive cancel-transaction
            if data['type'] == 'cancel':
                index = queue.index(data)
                transaction, last_client = queue.pop(index)
                last_client.send(pickle.dumps(
                    {{'msg': 'transaction canceled'}}))
                last_client.close()

                client.send(pickle.dumps({'msg': 'ok'}))
                client.close()
                continue

        from connect import table
        from_db = table.select(
            columns=['pk'],
            primaryKey_value=pk
        )

        if from_db != []:
            client.send(pickle.dumps({'msg': 'duplicate'}))
            continue

        queue.insert(len(queue), [data, client])


def poll_from_queue():
    """
    poll transaction and clint form queue
    and create Thread for jobs 
    """
    while True:
        while len(queue) > 0:
            transaction, client = queue.pop(0)
            thread = threading.Thread(
                target=handel, args=(transaction, client))
            thread.start()


if __name__ == "__main__":
    print('Gateway is running ...✅')
    rec = threading.Thread(target=receive, args=())
    rec.start()

    check = threading.Thread(target=poll_from_queue, args=())
    check.start()
