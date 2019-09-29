import socket
import threading
import time
import json
import pickle

#https://pypi.org/project/colorama/
from colorama import init, Fore, Back, Style

#Roughly based on https://rosettacode.org/wiki/Chat_server#Python with multiple changes and additions
#Also updated from Python2 to Python3

#Custom object to store all data being sent and received
class packIt:
    packNum = 0
    vNum = 0
    messType = 0
    channel = ""
    from_user = ""
    to_user = ""
    message = ""

    def __init__(self, packNum, vNum, messType, channel, from_user, to_user, message):
        self.packNum = packNum
        self.vNum = vNum
        self.messType = messType
        self.channel = channel
        self.from_user = from_user
        self.to_user = to_user
        self.message = message

#Send a packIt to the given socket
def sendPackIt(conn, packIt):
    global packetNum

    packToSend = pickle.dumps(packIt)
    conn.sendall(packToSend)
    packetNum += 1

#Accepts a connection from the client, runs through setup
def accept(conn, cli_addr):

    def threaded():
        while True:
            try:
                client_name = conn.recv(1024)
                client_name_data = pickle.loads(client_name)
                name = client_name_data.message
            except socket.error:
                continue
            #Check if username is already in use
            if name in users:
                packReply = packIt(packetNum, versionNum, 0, "", "SERVER", "", "")
                sendPackIt(conn, packReply)
            elif name:
                conn.setblocking(False)

                #Save the connection and name in a dictionary as well as the channel the user is in
                users[name] = conn
                usersChan[name] = channels[0]
                print("{0}: {1}".format(name, cli_addr))
                broadcast(name, Fore.YELLOW + "{0} has connected to the server.".format(name) + Style.RESET_ALL)
                broadcastChannel(name, Fore.WHITE + Style.DIM + "{0} has joined channel.".format(name) + Style.RESET_ALL, channels[0])
                
                replyMsg = Fore.GREEN + "You have successfully connected to the server." + Style.RESET_ALL
                packReplyMsg = packIt(packetNum, versionNum, 10, usersChan[name], "SERVER", name, replyMsg)
                sendPackIt(conn, packReplyMsg)
                break
    threading.Thread(target=threaded).start()

#Broadcast a message to all clients connected
def broadcast(name, message):
    print(message)
    for to_name, conn in users.items():
        if to_name != name:
            try:
                announce = Style.BRIGHT + Fore.RED + "SE" + Fore.BLUE + "RV" + Fore.MAGENTA + "ER" + Style.RESET_ALL
                msgToSend = "{0}: {1}".format(announce, message)
                packMsg = packIt(packetNum, versionNum, 10, "", "SERVER", to_name, msgToSend)
                sendPackIt(conn, packMsg)
            except socket.error:
                pass

#Broadcasts a message to a specific channel
def broadcastChannel(name, message, channel):

    print(message + "(Channel: {0})".format(channel))

    for user_name, curr_channel in usersChan.items():
        if channel.__eq__(curr_channel):
            if user_name != name:
                try:
                    packMsg = packIt(packetNum, versionNum, 10, channel, name, user_name, message)
                    sendPackIt(users[user_name], packMsg)
                except socket.error:
                    pass

#Broadcast a message to a specified user from another user (Private message)
def broadcastPrivateMsg(name, to_name, message):
    msg = "{0}@{1}=> {2}".format(name, to_name, message)

    #Check if the user actually exists
    if to_name in users:
        print(Fore.MAGENTA + msg + Style.RESET_ALL)
        try:
            packPvtMsg = packIt(packetNum, versionNum, 15, "", name, to_name, msg)
            sendPackIt(users[to_name], packPvtMsg)
        except socket.error:
            pass
    else:
        print(Fore.RED + "{0} attempted to send message to {1}: Error user doesn't exist.".format(name, to_name) + Style.RESET_ALL)
        replyMsg = Fore.RED + "Error: User {0} does not exist.".format(to_name) + Style.RESET_ALL
        try:
            packPvtMsg = packIt(packetNum, versionNum, 15, "", "SERVER", name, replyMsg)
            sendPackIt(users[name], packPvtMsg)
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

        broadcastChannel(name, Fore.WHITE + Style.DIM + partMsg + Style.RESET_ALL, usersChan[name])
        usersChan[name] = joinChannel

        broadcastChannel(name, Fore.WHITE + Style.DIM + joinMsg + Style.RESET_ALL, usersChan[name])
        replyMsg = Fore.GREEN + "You have successfully joined {0}.".format(usersChan[name]) + Style.RESET_ALL

        replyPack = packIt(packetNum, versionNum, 56, joinChannel, "SERVER", name, replyMsg)
        sendPackIt(users[name], replyPack)
    else:
        print(Fore.RED + "Unable to swap {0}'s channel; channel '{1}' does not exist.".format(name, joinChannel) + Style.RESET_ALL)
        
        replyMsg = Fore.RED + "SERVER: Unable to swap channels; channel does not exist." + Style.RESET_ALL
        replyPack = packIt(packetNum, versionNum, 55, "", "SERVER", name, replyMsg)
        sendPackIt(users[name], replyPack)

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

#Load server settings from settings.json
with open('settings.json') as f:
    json_data = json.load(f)

__server, __MAX_CONN = initializeServer()

users = {}
usersChan = {}
channels = json_data["channels"]

global packetNum
packetNum = 1
versionNum = json_data["Version"]

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
                packReject = packIt(packetNum, versionNum, 98, "", "SERVER", "", rejectMsg)
                sendPackIt(conn, packReject)
                conn.close()
            else:  
                accept(conn, addr)
        #
        for name, conn in users.items():
            try:
                message = conn.recv(4096)
                message_data = pickle.loads(message)

                print("Incoming packNum: {0}".format(message_data.packNum))
                print("Incoming vNum: {0}".format(message_data.vNum))
                print("Incoming Type: {0}".format(message_data.messType))

            except EOFError:
                continue
            except socket.error:
                continue

            #Standard broadcast message to all in user's channel
            if message_data.messType == 10:
                broadcastChannel(name, "{0}@{1}: {2}".format(name, usersChan[name], message_data.message), usersChan[name])
            #User request to join a different chat channel
            elif message_data.messType == 11:
                informServer(name, "join")
                swapChannel(name, message_data.message)
            #User requests a list of channels on the server
            elif message_data.messType == 12:
                informServer(name, "channels")
                reply = "Channels: "
                reply = reply + " ".join(str(e) for e in channels)
                packReply = packIt(packetNum, versionNum, 12, "", "SERVER", name, reply)
                sendPackIt(conn, packReply)
            #User requests a list of users in their current channel
            elif message_data.messType == 13:
                informServer(name, "whochan")
                chanToCompare = message_data.channel
                names = Style.BRIGHT + Fore.BLACK + Back.WHITE
                for _name, _chan in usersChan.items():
                    if chanToCompare.__eq__(_chan):
                        names = names + _name + ", "
                names = names + Style.RESET_ALL
                packReply = packIt(packetNum, versionNum, 13, "", "SERVER", name, names)
                sendPackIt(conn, packReply)
            #User requests a list of users connected to the server
            elif message_data.messType == 14:
                informServer(name, "who")
                names = Style.BRIGHT + Fore.BLACK + Back.WHITE
                for _name, _conn in users.items():
                    names = names + _name + ", "
                names = names + Style.RESET_ALL
                packReply = packIt(packetNum, versionNum, 14, "", "SERVER", name, names)
                sendPackIt(conn, packReply)
            #Send a private message to another user
            elif message_data.messType == 15:
                informServer(name, "whisper")
                broadcastPrivateMsg(name, message_data.to_user, message_data.message)
            #User disconnects from the server, delete their user data on the server
            elif message_data.messType == 99:
                del users[name]
                del usersChan[name]
                broadcast(name, Fore.RED + Style.DIM + "{0} has disconnected.".format(name) + Style.RESET_ALL)
                break

        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        __server.close()
        break