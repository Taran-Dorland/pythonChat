import socket
import threading
import json

#https://pypi.org/project/colorama/
from colorama import init, Fore, Back, Style

#Listens for incoming data from server
def incoming(conn):

    while True:
        try:
            message = conn.recv(1024)
            print(message.decode('utf-8'))
        except socket.error:
            print("Server connection error.")
            break

#Load client settings from settings.json
with open('C:\GitProjects\pythonchat\client\settings.json') as f:
    json_data = json.load(f)

#Establish connection to server
HOST = json_data["IP"]
PORT = json_data["PORT"]

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

msg1 = Fore.RED + "Test1"
msg2 = Fore.BLUE + "Test2"

print(msg1 + " " + msg2)

#First data being sent to the server is a username
while True:
    try:
        username = input("Enter a username: ")
        client.sendall(username.encode('utf-8'))

        reply = client.recv(1024)
        data = reply.decode('utf-8')

        if data.__eq__("0"):
            print("Name already in use.")
        else:
            break

    except socket.error:
        print("Error connecting to server.")
        exit()

#Create a thread to listen for messages coming from the server
listenThread = threading.Thread(target = incoming, args = (client, ))
listenThread.start()

#Client main features
while True:
    try:
        message = input("Enter your message: ")
        print("{0}>: {1}".format(username, message))
        client.sendall(message.encode('utf-8'))

    except (SystemExit, KeyboardInterrupt):
        break