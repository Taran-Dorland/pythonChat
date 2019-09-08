import socket
import threading
import time
import json

from colorama import init, Fore, Back, Style

#Roughly based on https://rosettacode.org/wiki/Chat_server#Python with multiple changes and additions
#Also updated from Python2 to Python3

def accept(conn):

    def threaded():
        while True:
            try:
                name = conn.recv(1024).decode('utf-8')
            except socket.error:
                continue
            #Check if username is already in use
            if name in users:
                conn.sendall("0".encode('utf-8'))
            elif name:
                conn.setblocking(False)

                #Save the connection and name in a dictionary as well as the channel the user is in
                users[name] = conn
                usersChan[name] = channels[0]
                broadcast(name, Fore.YELLOW + "{0} has connected to the server.".format(name) + Style.RESET_ALL)
                broadcastChannel(name, Fore.WHITE + Style.DIM + "{0} has joined channel.".format(name) + Style.RESET_ALL, channels[0])
                
                replyMsg = Fore.GREEN + "You have successfully connected to the server." + Style.RESET_ALL
                conn.sendall(replyMsg.encode('utf-8'))
                conn.sendall(usersChan[name].encode('utf-8'))
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

#Broadcasts a message to a specific channel
def broadcastChannel(name, message, channel):

    print(message)

    for user_name, curr_channel in usersChan.items():
        if channel.__eq__(curr_channel):
            if user_name != name:
                try:
                    users[user_name].sendall(message.encode('utf-8'))
                except socket.error:
                    pass

#Swaps a user's channel
def swapChannel(name, message):
    joinChannel = message[4:]
    channelExists = False

    #Check to see if the channel the user wants to join actually exists
    for channel in channels:
        if joinChannel.__eq__(channel):
            channelExists = True
    
    if channelExists == True:
        partMsg = "{0} has left the channel.".format(name)
        joinMsg = "{0} has joined the channel.".format(name)

        users[name].sendall("1".encode('utf-8'))

        broadcastChannel(name, Fore.WHITE + Style.DIM + partMsg + Style.RESET_ALL, usersChan[name])
        usersChan[name] = joinChannel

        broadcastChannel(name, Fore.WHITE + Style.DIM + joinMsg + Style.RESET_ALL, usersChan[name])
    else:
        print(Fore.RED + "Unable to swap {0}'s channel; channel does not exist.".format(name) + Style.RESET_ALL)
        #Error 155: UNABLE TO SWAP CHANNELS
        users[name].sendall("155".encode('utf-8'))
        users[name].sendall(Fore.RED + "SERVER: Unable to swap channels; channel does not exist." + Style.RESET_ALL.encode('utf-8'))

#Setup the server to the specified IP and Port in settings.json
def initializeServer():
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

    return server, MAX_CONN

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

__server, __MAX_CONN = initializeServer()

users = {}
usersChan = {}
channels = json_data["channels"]

while True:
    try:
        #
        while True:
            try:
                conn, addr = __server.accept()
            except socket.error:
                break

            #ONLY ALLOW A CERTAIN NUMBER OF CONNECTIONS TO THE SERVER
            if len(users) >= __MAX_CONN:
                rejectMsg = Fore.RED + "SERVER: Connection refused. Server is full." + Style.RESET_ALL
                conn.sendall(rejectMsg.encode('utf-8'))
                conn.close()
            else:  
                accept(conn)
        #
        for name, conn in users.items():
            try:
                message = conn.recv(1024).decode('utf-8')
            except socket.error:
                continue
            if not message:
                #
                del users[name]
                del usersChan[name]
                broadcast(name, Fore.RED + Style.DIM + "{0} has disconnected.".format(name) + Style.RESET_ALL)
                break
            else:
                if message[:4].__eq__("join"):
                    swapChannel(name, message)
                else:
                    broadcastChannel(name, "{0}@{1}: {2}".format(name, usersChan[name], message, usersChan[name]))
        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        __server.close()
        break