import socket
import threading
import time
import json

#Load client settings from settings.json
with open('C:\GitProjects\pythonchat\client\settings.json') as f:
    json_data = json.load(f)

HOST = json_data["IP"]
PORT = json_data["PORT"]

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

while True:
    try:
        message = input("Enter your message: ")
        print(message)
        client.sendall(message.encode('utf-8'))

        reply = client.recv(1024)
        print(reply)
    except (SystemExit, KeyboardInterrupt):
        break