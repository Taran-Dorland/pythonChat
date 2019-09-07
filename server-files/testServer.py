import socket
import threading
import time
import json

from colorama import init, Fore, Back, Style

#Roughly based on https://rosettacode.org/wiki/Chat_server#Python with multiple changes and additions

def accept(conn):

    def threaded():
        while True:
            try:
                name = conn.recv(1024).strip()
            except socket.error:
                continue
            #Check if username is already in use
            if name in users:
                conn.sendall("0".encode('utf-8'))
            elif name:
                conn.setblocking(False)
                users[name] = conn
                broadcast(name, Fore.YELLOW + "{0} has connected.".format(name) + Style.RESET_ALL)
                
                replyMsg = Fore.GREEN + "You have successfully connected to the server." + Style.RESET_ALL
                conn.sendall(replyMsg.encode('utf-8'))
                break
    threading.Thread(target=threaded).start()

#Broadcast a message to all clients connected
def broadcast(name, message):
    print(message)
    for to_name, conn in users.items():
        if to_name != name:
            try:
                conn.sendall("SERVER: {0}".format(message).encode('utf-8'))
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
print("SERVER: Listening on {0}".format(server.getsockname()))

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
            if len(users) >= MAX_CONN:
                rejectMsg = Fore.RED + "SERVER: Connection refused. Server is full." + Style.RESET_ALL
                conn.sendall(rejectMsg.encode('utf-8'))
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
                broadcast(name, Fore.RED + Style.DIM + "{0} has disconnected.".format(name) + Style.RESET_ALL)
                break
            else:
                broadcast(name, "{0}>: {1}".format(name, message.strip()))
        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        server.close()
        break