import socket
import threading
import time
import json

#Roughly based on https://rosettacode.org/wiki/Chat_server#Python with multiple changes and additions

def accept(conn):

    def threaded():
        while True:
            try:
                name = conn.recv(1024).strip()
            except socket.error:
                continue
            if name in users:
                conn.send("SERVER: Name already in use.\n")
            elif name:
                conn.setblocking(False)
                users[name] = conn
                broadcast(name, "${0} has connected.".format(name))
                break
    threading.Thread(target=threaded).start()

#Broadcast a message to all clients connected
def broadcast(name, message):
    print(message)
    for to_name, conn in users.items():
        if to_name != name:
            try:
                conn.send("SERVER: ", message, "\n")
            except socket.error:
                pass

#Get host machine IP
#Best way would be to set static IP and change server settings in settings.json
serverIp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverIp.connect(("8.8.8.8", 80))
HOST_IP = serverIp.getsockname()[0]
serverIp.close()
print(HOST_IP)

#Load server settings from settings.json
with open('settings.json') as f:
    json_data = json.load(f)

HOST = json_data["IP"]
PORT = json_data["PORT"]
MAX_CONN = json_data["MAX_CONNECTIONS"]

#Info for AF_INET and SOCK_STREAM
#https://docs.python.org/3/library/socket.html
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)
server.bind((HOST, PORT))
server.listen(1)
print("SERVER: Listening on ${0}".format(server.getsockname()))

users = {}

while True:
    try:
        #
        while True:
            try:
                conn, addr = server.accept()
            except socket.error:
                break

            #ONLY ALLOW A CERTAIN NUMBER OF CONNECTIONS TO THE SERVER
            if len(users) == MAX_CONN:
                conn.send("SERVER: Server is full.\n")
                conn.close()
            else:  
                accept(conn)
        #
        for name, conn in users.items():
            try:
                message = conn.recv(1024)
            except socket.error:
                continue
            if not message:
                #
                del users[name]
                broadcast(name, name % " has disconnected.")
            else:
                broadcast(name, "%s> %s" % (name, message.strip()))
        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        break