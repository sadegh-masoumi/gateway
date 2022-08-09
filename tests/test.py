import socket
# import json
import pickle


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(('127.0.0.1', 8080))


data = {
    "pk": 12344,
    "type": "accept",
    "content": "x",
    "canceled": False
}
client.send(pickle.dumps(data))
