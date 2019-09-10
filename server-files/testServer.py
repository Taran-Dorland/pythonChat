import socket
import threading
import time
import json

#https://pypi.org/project/colorama/
from colorama import init, Fore, Back, Style

#Roughly based on https://rosettacode.org/wiki/Chat_server#Python with multiple changes and additions
#Also updated from Python2 to Python3

#Accepts a connection from the client, runs through setup
def accept(conn, cli_addr):

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
                print("{0}: {1}".format(name, cli_addr))
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
                announce = Style.BRIGHT + Fore.RED + "SE" + Fore.BLUE + "RV" + Fore.MAGENTA + "ER" + Style.RESET_ALL
                conn.sendall("{0}: {1}".format(announce, message).encode('utf-8'))
            except socket.error:
                pass

#Broadcasts a message to a specific channel
def broadcastChannel(name, message, channel):

    print(message + "(Channel: {0})".format(channel))

    for user_name, curr_channel in usersChan.items():
        if channel.__eq__(curr_channel):
            if user_name != name:
                try:
                    users[user_name].sendall(message.encode('utf-8'))
                except socket.error:
                    pass

#Broadcast a message to a specified user from another user (Private message)
def boradcastPrivateMsg(name, to_name, message):
    msg = Fore.MAGENTA + "{0}@{1}=> {2}".format(name, to_name, message) + Style.RESET_ALL
    print(msg)

    if users[to_name] is None:
        print(Fore.RED + "{0} attempted to send message to {1}: Error user doesn't exist.".format(name, to_name))
        replyMsg = Fore.RED + "Error: User {0} does not exist.".format(to_name) + Style.RESET_ALL
        try:
            users[name].sendall(replyMsg.encode('utf-8'))
        except socket.error:
            pass
    else:
        try:
            users[to_name].sendall(msg.encode('utf-8'))
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
        replyMsg = Fore.GREEN + "You have successfully joined {0}.".format(usersChan[name]) + Style.RESET_ALL
        users[name].sendall(replyMsg.encode('utf-8'))
    else:
        print(Fore.RED + "Unable to swap {0}'s channel; channel '{1}' does not exist.".format(name, joinChannel) + Style.RESET_ALL)
        #Error 155: UNABLE TO SWAP CHANNELS
        users[name].sendall("155".encode('utf-8'))
        replyMsg = Fore.RED + "SERVER: Unable to swap channels; channel does not exist." + Style.RESET_ALL
        users[name].sendall(replyMsg.encode('utf-8'))

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

#Prints information to server terminal
def informServer(name, command):
    print(Fore.CYAN + Style.BRIGHT + "{0} issued command '{1}' on server.".format(name, command) + Style.RESET_ALL)

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
                accept(conn, addr)
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
                #Let the user request to join a specific channel
                if message[:4].__eq__("join"):
                    informServer(name, "join")
                    swapChannel(name, message)
                #Return a list of channels to the user
                elif message.__eq__("chan"):
                    informServer(name, "channels")
                    reply = "Channels: "
                    reply = reply + " ".join(str(e) for e in channels)
                    conn.sendall(reply.encode('utf-8'))
                #Return a string of users in a specified channel
                elif message[:8].__eq__("whochan_"):
                    informServer(name, "whochan")
                    chanToComp = message[8:]
                    names = Style.BRIGHT + Fore.BLACK + Back.WHITE
                    for _name, _chan in usersChan.items():
                        if chanToComp.__eq__(_chan):
                            names = names +  _name + ", "
                    names = names + Style.RESET_ALL
                    conn.sendall(names.encode('utf-8'))
                #Return a string of users who are connected to the server
                elif message.__eq__("who"):
                    informServer(name, "who")
                    names = Style.BRIGHT + Fore.BLACK + Back.WHITE
                    for _name, _conn in users.items():
                        names = names +  _name + ", "
                    names = names + Style.RESET_ALL
                    conn.sendall(names.encode('utf-8'))
                #Command to send a message to a specific user
                elif message[:2].__eq__("w_"):
                    informServer(name, "whisper")
                    cmdMsg = message.split('_')
                    boradcastPrivateMsg(name, cmdMsg[1], cmdMsg[2])
                else:
                    broadcastChannel(name, "{0}@{1}: {2}".format(name, usersChan[name], message), usersChan[name])
        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        __server.close()
        break