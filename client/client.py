import socket
import threading
import time
import json
import pickle

#https://pypi.org/project/colorama/
from colorama import init, Fore, Back, Style

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
        

#Listens for incoming data from server
def incoming(conn):

    global __curChannel, __prevChannel, __prevWhisper

    while True:
        try:
            message = conn.recv(4096)
            message_data = pickle.loads(message)
            
            #Standard message from channel
            if message_data.messType == 10:
                print(message_data.message)
            #Server reply for list of channels
            elif message_data.messType == 12:
                print(message_data.message)
            #Server reply for list of users in channel
            elif message_data.messType == 13:
                print(message_data.message)
            #Server reply for list of users in server
            elif message_data.messType == 14:
                print(message_data.message)
            #Private message from another user
            elif message_data.messType == 15:
                print(message_data.message)
                __prevWhisper = message_data.from_user
            #Failed to join server channel, channel does not exist
            elif message_data.messType == 55:
                print(message_data.message)
            #Confirmation message for changing chat channels
            elif message_data.messType == 56:
                print(message_data.message)
                __prevChannel = __curChannel
                __curChannel = message_data.channel
            #Failed to sent a private message to a user, user doesn't exist
            elif message_data.messType == 57:
                print(message_data.message)

        except socket.error:
            print("Server connection lost.")
            break

#Outputs a list of commands that the user can enter in the chat
def listCommands():
    print("List of commands: ")
    print("/w 'user' 'message'\t:Send a private message to another user.")
    print("/r 'message'\t\t:Send a private message to last user to whisper you.")
    print("/who\t\t\t:Lists current users connected to the server.")
    print("/whochan\t\t:Lists current users in your channel.")
    print("/channels\t\t:Returns a list of channels on the server.")
    print("/join 'channel'\t\t:User joins the specified channel. User can only be in one channel at a time.")
    print("/conn\t\t\t:Connects to the server.")
    print("/dc\t\t\t:Disconnects from the server.")
    print("/quit\t\t\t:Disconnects from the server and exits the program.\n")

#Lets the user select a username, will reject if that username is already registered on the server
def enterUsername(conn):
    #First data being sent to the server is a username
    while True:
        try:
            username = input("Enter a username: ")
            conn.sendall(username.encode('utf-8'))

            reply = conn.recv(1024)
            data = reply.decode('utf-8')

            if data.__eq__("0"):
                print(Fore.RED + "Name already in use." + Style.RESET_ALL)
            else:
                print(data)
                channel = conn.recv(1024).decode('utf-8')
                return username, channel

        except socket.error:
            print("Server connection lost.")
            exit()

#For auto-login
def autoUsername(conn, username):
    while True:
        try:
            conn.sendall(username.encode('utf-8'))

            reply = conn.recv(1024)
            data = reply.decode('utf-8')

            if data.__eq__("0"):
                print(Fore.RED + "Name already in use. Disconnecting..." + Style.RESET_ALL)
                conn.close()
            else:
                print(data)
                channel = conn.recv(1024).decode('utf-8')
                return username, channel

        except socket.error:
            print("Server connection lost.")
            exit()

#Connects the user to the server specified by the IP and Port entered in settings.json
def connectToServer():
    #Establish connection to server
    HOST = json_data["IP"]
    PORT = json_data["PORT"]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    #Check auto-connect settings in settings.json
    auto_Connect = json_data["auto-connect"]

    if auto_Connect == False:
        username, channel = enterUsername(client)
    else:
        username, channel = autoUsername(client, json_data["username"])

    #Create a thread to listen for messages coming from the server
    listenThread = threading.Thread(target = incoming, args = (client, ))
    listenThread.start()

    return client, username, channel

#Send a packit to the server
def sendPackIt(packIt, pNum):
    packToSend = pickle.dumps(packIt)
    __client.sendall(packToSend)

    return pNum + 1

#Load client settings from settings.json
with open('C:\GitProjects\pythonchat\client\settings.json') as f:
    json_data = json.load(f)

global __curChannel, __prevChannel, __prevWhisper
__client, __username, __curChannel = connectToServer()
__prevChannel = __curChannel

#Packet info
packetNum = 1
versionNum = 1.0

#Client main
while True:
    try:
        #https://stackoverflow.com/questions/10829650/delete-the-last-input-row-in-python
        message = input("Enter your message: ")
        print("\033[A                             \033[A")

        #Join a chat channel on the server
        if message[:5].__eq__("/join"):
            channel = message[6:]
            packJoin = packIt(packetNum, versionNum, 11, __curChannel, __username, "", channel)
            packetNum = sendPackIt(packJoin, packetNum)
            time.sleep(.25)
        #View the channels available on the server
        elif message.__eq__("/channels"):
            packChan = packIt(packetNum, versionNum, 12, __curChannel, __username, "", "")
            packetNum = sendPackIt(packChan, packetNum)
            time.sleep(.25)
        #View all users in your current chat channel
        elif message.__eq__("/whochan"):
            packChan = packIt(packetNum, versionNum, 13, __curChannel, __username, "", "")
            packetNum = sendPackIt(packChan, packetNum)
            time.sleep(.25)
        #View all users connected to the server
        elif message.__eq__("/who"):
            packWho = packIt(packetNum, versionNum, 14, __curChannel, __username, "", "")
            packetNum = sendPackIt(packWho)
            time.sleep(.25)
        #Send a private message to a user on the server
        elif message[:2].__eq__("/w"):
            msgToSend = Fore.MAGENTA + message + Style.RESET_ALL
            msg = message.split(' ')
            packWhisp = packIt(packetNum, versionNum, 15, __curChannel, __username, msg[1], msgToSend)
            packetNum = sendPackIt(packWhisp, packetNum)
            time.sleep(.25)
        #Reply to the last user who send you a private message
        elif message[:2].__eq__("/r"):
            msgToSend = Fore.MAGENTA + message + Style.RESET_ALL
            msg = message.split(' ')
            packWhisp = packIt(packetNum, versionNum, 15, __curChannel, __username, __prevWhisper, msgToSend)
            packetNum = sendPackIt(packWhisp, packetNum)
            time.sleep(.25)
        #Lists the available commands
        elif message.__eq__("/help"):
            listCommands()
        #Disconnects from the server
        elif message.__eq__("/dc"):
            __client.close()
        #Connects to the server
        elif message.__eq__("/conn"):
            __client = connectToServer
        #Disconnect from the server, exit the client
        elif message.__eq__("/quit"):
            __client.close()
            exit()
        #Send a standard message to the current channel on the server
        else:
            print("{0}@{1}: {2}".format(__username, __curChannel, message))
            packMsg = packIt(packetNum, versionNum, 10, __curChannel, __username, "", message)
            packetNum = sendPackIt(packMsg, packetNum)

    except (SystemExit, KeyboardInterrupt):
        break