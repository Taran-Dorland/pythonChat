#   --------------------------------------------------------------------------------------------
#   Server application for a basic chat application built in python3
#   Name:           server.py
#   Written by:     Taran Dorland
#   Purpose:        Handles client connections and the distribution and receiving of
#                   text-based data between clients.
#   Usage:          When started, listens for clients connecting to the current IP address
#                   and Port through a TCP socket. It then receives text-based data from
#                   clients and distributes it between other connected clients.
#   Description of
#   parameters:     Parameters are customizable through the settings.json file in the same
#                   directory as server.py:
#                   ----------------------------------------------------------------------------
#                   Version:        Sets the server version number
#                   IP:             Set the IP to match the IP of the current machine
#                                   (Leave as localhost to get it automatically)
#                   Port:           Set the port number for which clients should connect through
#                   MaxConnections: Sets the max amount of clients allowed to connect to the
#                                   server at a tiume
#                   Channels{}:     An array of channel names to be setup on the server. Channels
#                                   are esentially chat rooms, allowing users to join different
#                                   channels allows for users to have different conversations
#                                   without interfering with other conversations
#   
#   Libraries
#   required:       Python imports:
#                   socket:     Used to open a socket to allow connections to other devices
#                   threading:  Used to allow multiple threads so connections are quicker
#                   time:       Used to make threads wait
#                   json:       Used to import server settings.json file
#                   pickle:     Serializer used to pack and unpack python objects to send multiple
#                               pieces of data together
#                   hashlib:    Used to generate a checksum hash, currently using SHA256
# 
#                   3rd-Party imports:
#                   Colorama:
#                       Desc:   Makes ANSI escape character sequences (for producing colored terminal 
#                               text and cursor positioning) work under MS Windows.
#                       Link:   https://pypi.org/project/colorama/
#
#   Other:          Roughly based on https://rosettacode.org/wiki/Chat_server#Python with multiple
#                   changes and additions also updated from Python2 to Python3
#   --------------------------------------------------------------------------------------------

import socket
import threading
import time
import json
import pickle
#https://docs.python.org/3/library/hashlib.html
import hashlib
import codecs
#https://docs.python.org/3/library/codecs.html

from colorama import init, Fore, Back, Style

#Custom object to store all data being sent and received
class packIt:
    packNum = 0
    vNum = 0
    messType = 0
    channel = ""
    from_user = ""
    to_user = ""
    message = ""
    checkSum = ""
    encrypted = True

    #Constructor
    def __init__(self, packNum, vNum, messType, channel, from_user, to_user, message, checkSum, encrypted):
        self.packNum = packNum
        self.vNum = vNum
        self.messType = messType
        self.channel = channel
        self.from_user = from_user
        self.to_user = to_user
        self.message = message
        self.checkSum = checkSum
        self.encrypted = encrypted

#Send a packIt object to the given connection
def sendPackIt(conn, packIt):
    global packetNum

    try:
        messageHash = hashlib.sha256(str(packIt.message).encode('utf-8')).hexdigest()
        packIt.checkSum = messageHash
    except NameError:
        print("Data in 'message' field is not defined. Not adding CheckSum.")
        packIt.checkSum = 0

    packToSend = pickle.dumps(packIt)
    conn.sendall(packToSend)
    packetNum += 1

#Accepts a connection from the client, runs through setup
def accept(conn, cli_addr):

    def threaded():
        while True:
            #Client connection handshake
            try:
                client_name = conn.recv(1024)
                client_name_data = pickle.loads(client_name)
                name = client_name_data.message
            except socket.error:
                continue
            #Check if username is already in use
            if name in users:
                #Username already in use
                packReply = packIt(packetNum, versionNum, 0, "", "SERVER", "", "Name already in use.", "", False)
                sendPackIt(conn, packReply)
            elif name:
                conn.setblocking(False)

                #Save the connection and name in a dictionary as well as the channel the user is in
                users[name] = conn
                usersChan[name] = channels[0]
                print("{0}: {1}".format(name, cli_addr))
                broadcast(name, Fore.YELLOW + "{0} has connected to the server.".format(name) + Style.RESET_ALL, False)
                broadcastChannel(name, Fore.WHITE + Style.DIM + "{0} has joined channel.".format(name) + Style.RESET_ALL, channels[0], False)
                
                replyMsg = Fore.GREEN + "You have successfully connected to the server." + Style.RESET_ALL
                packReplyMsg = packIt(packetNum, versionNum, 10, usersChan[name], "SERVER", name, replyMsg, "", True)
                sendPackIt(conn, packReplyMsg)
                break
    threading.Thread(target=threaded).start()

#Broadcast a message to all clients connected
def broadcast(name, message, encrypted):
    print(message)

    #Sends the message to all clients currently connected to the server except for the clien that sent it
    for to_name, conn in users.items():
        if to_name != name:
            try:
                announce = Style.BRIGHT + Fore.RED + "SE" + Fore.BLUE + "RV" + Fore.MAGENTA + "ER" + Style.RESET_ALL
                msgToSend = "{0}: {1}".format(announce, message)
                packMsg = packIt(packetNum, versionNum, 10, "", "SERVER", to_name, msgToSend, "", encrypted)
                sendPackIt(conn, packMsg)
            except socket.error:
                pass

#Broadcasts a message to a specific channel
def broadcastChannel(name, message, channel, encrypted):

    print(message + "(Channel: {0})".format(channel))

    #Sends the message to everyone in the specified channel except the user who sent it
    for user_name, curr_channel in usersChan.items():
        if channel.__eq__(curr_channel):
            if user_name != name:
                try:
                    packMsg = packIt(packetNum, versionNum, 10, channel, name, user_name, message, "", encrypted)
                    sendPackIt(users[user_name], packMsg)
                except socket.error:
                    pass

#Broadcast a message to a specified user from another user (Private message)
def broadcastPrivateMsg(name, to_name, message, encrypted):
    #Check if the user actually exists
    if to_name in users:
        print(message)
        try:
            packPvtMsg = packIt(packetNum, versionNum, 15, "", name, to_name, message, "", encrypted)
            sendPackIt(users[to_name], packPvtMsg)
        except socket.error:
            pass
    else:
        #USER DOESN'T EXIST; SEND ERROR MESSAGE
        print(Fore.RED + "{0} attempted to send message to {1}: Error user doesn't exist.".format(name, to_name) + Style.RESET_ALL)
        replyMsg = Fore.RED + "Error: User {0} does not exist.".format(to_name) + Style.RESET_ALL
        try:
            packPvtMsg = packIt(packetNum, versionNum, 15, "", "SERVER", name, replyMsg, "", False)
            sendPackIt(users[name], packPvtMsg)
        except socket.error:
            pass

#Swaps a user's channel
def swapChannel(name, message):
    joinChannel = message
    channelExists = False

    #Check to see if the channel the user wants to join actually exists
    for channel in channels:
        if joinChannel.__eq__(channel):
            channelExists = True
    
    if channelExists == True:
        #Notifications
        partMsg = "{0} has left the channel.".format(name)
        joinMsg = "{0} has joined the channel.".format(name)

        #Broadcast notifications to correct channels
        broadcastChannel(name, Fore.WHITE + Style.DIM + partMsg + Style.RESET_ALL, usersChan[name], False)
        usersChan[name] = joinChannel

        broadcastChannel(name, Fore.WHITE + Style.DIM + joinMsg + Style.RESET_ALL, usersChan[name], False)
        replyMsg = Fore.GREEN + "You have successfully joined {0}.".format(usersChan[name]) + Style.RESET_ALL

        #User joines the specified channel
        replyPack = packIt(packetNum, versionNum, 56, joinChannel, "SERVER", name, replyMsg, "", False)
        sendPackIt(users[name], replyPack)
    else:
        #CHANNEL DOESN'T EXIST; SEND ERROR MESSAGE
        print(Fore.RED + "Unable to swap {0}'s channel; channel '{1}' does not exist.".format(name, joinChannel) + Style.RESET_ALL)
        
        replyMsg = Fore.RED + "SERVER: Unable to swap channels; channel does not exist." + Style.RESET_ALL
        replyPack = packIt(packetNum, versionNum, 55, "", "SERVER", name, replyMsg, "", False)
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

#Decrypts the incoming message for the purpose of the assignment
def snoopMessage(message):
    return codecs.decode(message, "rot-13")

#Load server settings from settings.json
with open('settings.json') as f:
    json_data = json.load(f)

__server, __MAX_CONN = initializeServer()

#Setup initial server settings
users = {}
usersChan = {}
channels = json_data["channels"]

global packetNum
packetNum = 0
packetNum = 1
versionNum = json_data["Version"]

#MAIN SERVER LOOP LISTENING FOR INCOMING DATA AND CONNECTIONS
while True:
    try:
        while True:
            try:
                conn, addr = __server.accept()
            except socket.error:
                break

            #ONLY ALLOW A CERTAIN NUMBER OF CONNECTIONS TO THE SERVER
            if len(users) >= __MAX_CONN:
                rejectMsg = Fore.RED + "SERVER: Connection refused. Server is full." + Style.RESET_ALL
                packReject = packIt(packetNum, versionNum, 98, "", "SERVER", "", rejectMsg, "", False)
                sendPackIt(conn, packReject)
                conn.close()
            else:
                accept(conn, addr)
        #Received incoming data, parse it and decide what to do with it
        for name, conn in users.items():
            try:
                message = conn.recv(4096)
                #Load pickled object; will automatically set it as a packIt() object
                message_data = pickle.loads(message)

                print("")
                print("Incoming packNum: {0}".format(message_data.packNum))
                print("Incoming vNum: {0}".format(message_data.vNum))
                print("Incoming Type: {0}".format(message_data.messType))
                print("Incoming checkSum: {0}".format(message_data.checkSum))

                #CHECK DATA CHECKSUM
                try:
                    incomingCheckSum = message_data.checkSum
                    comparableCheckSum = hashlib.sha256(str(message_data.message).encode('utf-8')).hexdigest()
                    print("Actual checkSum: {0}".format(comparableCheckSum))

                    if comparableCheckSum.__eq__(incomingCheckSum):
                        print(Fore.GREEN + "CheckSum verification successful." + Style.RESET_ALL)
                    else:
                        print(Fore.RED + "CheckSum verification failed. Requesting data again.." + Style.RESET_ALL)
                        packFailed = packIt(packetNum, versionNum, 90, "", "SERVER", name, str(message_data.packNum), "", False)
                        sendPackIt(conn, packFailed)
                        break
                    
                except NameError:
                    print("Incoming data does not have a defined CheckSum.")

            except EOFError:
                continue
            except socket.error:
                continue

            #Standard broadcast message to all in user's channel
            if message_data.messType == 10:
                broadcastChannel(name, "{0}@{1}: {2}".format(name, usersChan[name], message_data.message), usersChan[name], message_data.encrypted)
                if message_data.encrypted == True:
                    print("(DECRYPTED){0}@{1}: {2}".format(name, usersChan[name], snoopMessage(message_data.message)))
            #User request to join a different chat channel
            elif message_data.messType == 11:
                informServer(name, "join")
                swapChannel(name, message_data.message)
            #User requests a list of channels on the server
            elif message_data.messType == 12:
                informServer(name, "channels")
                reply = "Channels: "
                reply = reply + " ".join(str(e) for e in channels)
                packReply = packIt(packetNum, versionNum, 12, "", "SERVER", name, reply, "", False)
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
                packReply = packIt(packetNum, versionNum, 13, "", "SERVER", name, names, "", False)
                sendPackIt(conn, packReply)
            #User requests a list of users connected to the server
            elif message_data.messType == 14:
                informServer(name, "who")
                names = Style.BRIGHT + Fore.BLACK + Back.WHITE
                for _name, _conn in users.items():
                    names = names + _name + ", "
                names = names + Style.RESET_ALL
                packReply = packIt(packetNum, versionNum, 14, "", "SERVER", name, names, "", False)
                sendPackIt(conn, packReply)
            #Send a private message to another user
            elif message_data.messType == 15:
                informServer(name, "whisper")
                broadcastPrivateMsg(name, message_data.to_user, message_data.message, message_data.encrypted)
                if message_data.encrypted == True:
                    print("(DECRYPTED){0}".format(snoopMessage(message_data.message)))
            #User disconnects from the server, delete their user data on the server
            elif message_data.messType == 99:
                informServer(name, "disconnect")
                packReply = packIt(packetNum, versionNum, 99, "", "SERVER", name, "Closing connection.", "", False)
                sendPackIt(conn, packReply)
                del users[name]
                del usersChan[name]
                broadcast(name, Fore.RED + Style.DIM + "{0} has disconnected.".format(name) + Style.RESET_ALL, message_data.encrypted)
                break

        time.sleep(.1)
    except (SystemExit, KeyboardInterrupt):
        __server.close()
        break