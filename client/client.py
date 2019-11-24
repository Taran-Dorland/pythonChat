#   --------------------------------------------------------------------------------------------
#   Client application for a basic chat application built in python3
#   Name:           client.py
#   Written by:     Taran Dorland
#   Purpose:        Connects to the desired server and allows the user to send text-data
#                   to other clients also connected to the server.
#   Usage:          When started, attempts to connect to specified server in the settings.json
#                   file. It then listens for user input for which data is sent to the server
#                   to be processed and distributed appropriately.
#   Description of
#   parameters:     Parameters are customizable through the settings.json file in the same
#                   directory as client.py:
#                   ----------------------------------------------------------------------------
#                   Version:        Sets the client version number
#                   IP:             Sets the IP of the server to connect to
#                   Port:           Sets the Port of the server to connect to
#                   Auto-Connect:   Sets whether the client should auto-connect to the server
#                                   on startup
#                   Username:       Sets the username to auto-connect with
#   
#   Libraries
#   required:       Python imports:
#                   sys:        Used for printing unique commands to clear printed lines
#                   socket:     Used to open a socket to allow connections to other devices
#                   threading:  Used to allow multiple threads to listen for incoming data and
#                               send outgoing data
#                   time:       Used to make threads wait
#                   json:       Used to import client settings.json file
#                   pickle:     Serializer used to pack and unpack python objects to send multiple
#                               pieces of data together
#                   random:     Used to generate random numbers
#                   hashlib:    Used to generate a checksum hash, currently using SHA256
# 
#                   3rd-Party imports:
#                   Colorama:
#                       Desc:   Makes ANSI escape character sequences (for producing colored terminal 
#                               text and cursor positioning) work under MS Windows.
#                       Link:   https://pypi.org/project/colorama/
#   --------------------------------------------------------------------------------------------

import sys
import socket
import threading
import time
import json
import pickle
import random
#https://docs.python.org/3/library/hashlib.html
import hashlib

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

    #Constructor
    def __init__(self, packNum, vNum, messType, channel, from_user, to_user, message, checkSum):
        self.packNum = packNum
        self.vNum = vNum
        self.messType = messType
        self.channel = channel
        self.from_user = from_user
        self.to_user = to_user
        self.message = message
        self.checkSum = checkSum
        
#Listens for incoming data from server (threaded)
def incoming(conn):

    global __curChannel, __prevChannel, __prevWhisper
    global packetNum

    while True:
        try:
            message = conn.recv(4096)
            message_data = pickle.loads(message)
            
            #Standard message from channel
            if message_data.messType == 10:
                #Deletes the previous line so it's easier to read what was said
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
            #Server reply for list of channels
            elif message_data.messType == 12:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
            #Server reply for list of users in channel
            elif message_data.messType == 13:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
            #Server reply for list of users in server
            elif message_data.messType == 14:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
            #Private message from another user
            elif message_data.messType == 15:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
                __prevWhisper = message_data.from_user
            #Failed to join server channel, channel does not exist
            elif message_data.messType == 55:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
            #Confirmation message for changing chat channels
            elif message_data.messType == 56:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
                __prevChannel = __curChannel
                __curChannel = message_data.channel
            #Failed to sent a private message to a user, user doesn't exist
            elif message_data.messType == 57:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
            #Checksum verification failed on server; Requesting the packIt() again
            elif message_data.messType == 90:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print("Checksum verification failed on server; Must send previous packIt again.")
                print("")

                #Resend the correct packIt()
                resendPackNum = int(message_data.message)

                for pack in packArray:
                    if pack.packNum == resendPackNum:
                        packToResend = pack
                        break

                print("Resending packet with packet number: {0}".format(resendPackNum))

                packArray.append(packToResend)
                packetNum = sendPackIt(packToResend, packetNum)

            #Return packet to disconnect from server
            elif message_data.messType == 99:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print(message_data.message)
                print("")
                conn.close()
                break

        except EOFError:
            print("EOF Error, disconnecting..")
            conn.close()
            pass
        except socket.error:
            print("Server connection lost.")
            print("Use /conn to attempt to reconnect to the server.")
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
    print("/encrypt\t\t\t:Toggles encryption on outgoing messages.")
    print("/conn\t\t\t:Connects to the server.")
    print("/dc\t\t\t:Disconnects from the server.")
    print("/quit\t\t\t:Disconnects from the server and exits the program.\n")

#Lets the user select a username, will reject if that username is already registered on the server
def enterUsername(conn, packNum, vNum):
    #First data being sent to the server is a username
    while True:
        try:
            username = input("Enter a username: ")
            packLogin = packIt(packNum, vNum, 25, "", username, "", username, "")
            packArray.append(packLogin)
            packToSend = pickle.dumps(packLogin)
            conn.sendall(packToSend)
            packNum += 1

            reply = conn.recv(1024)
            reply_data = pickle.loads(reply)

            #Check if username is already in use
            if reply_data.messType == 0:
                print(Fore.RED + "Name already in use." + Style.RESET_ALL)
            else:
                print(reply_data.message)
                channel = reply_data.channel
                return username, channel, packNum

        except socket.error:
            print("Server connection lost.")
            exit()

#For auto-login if set to true in settings.json
def autoUsername(conn, username, packNum, vNum):
    try:
        channel = ""
        packAutoLogin = packIt(packNum, vNum, 25, "", username, "", username, "")
        packArray.append(packAutoLogin)
        packToSend = pickle.dumps(packAutoLogin)
        conn.sendall(packToSend)
        packNum += 1

        reply = conn.recv(1024)
        reply_data = pickle.loads(reply)

        #Check if username is already in use, if it is switch to manual input of username at enterUsername()
        if reply_data.messType == 0:
            print(Fore.RED + "Name already in use. Switching to manual..." + Style.RESET_ALL)
            username, channel, packNum = enterUsername(conn, packNum, vNum)
        else:
            print(reply_data.message)
            channel = reply_data.channel

        return username, channel, packNum

    except socket.error:
        print("Server connection lost.")
        exit()

#Connects the user to the server specified by the IP and Port entered in settings.json
def connectToServer(packNum, vNum):
    #Establish connection to server
    HOST = json_data["IP"]
    PORT = json_data["PORT"]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    #Check auto-connect settings in settings.json
    auto_Connect = json_data["auto-connect"]

    if auto_Connect == False:
        username, channel, packNum = enterUsername(client, packNum, vNum)
    else:
        username, channel, packNum = autoUsername(client, json_data["username"], packNum, vNum)

    #Create a thread to listen for messages coming from the server
    listenThread = threading.Thread(target = incoming, args = (client, ))
    listenThread.start()

    return client, username, channel, packNum

#Calculates the checksum on the packIt message data and adds it to the packIt()
#Then sends that packIt() to the server
def sendPackIt(packIt, pNum, encrypt):

    #Artificial checksum corruption
    rand = random.randint(0, 9)

    #Don't corrupt checksum
    if rand >= 1:
        #Calculate the checksum to be added to the header of the packIt()
        try:
            messageHash = hashlib.sha256(str(packIt.message).encode('utf-8')).hexdigest()
            packIt.checkSum = messageHash
        except NameError:
            print("Data in 'message' field is not defined. Failed to calculate checksum.")
            packIt.checkSum = "Undefined"
    #Corrupt checksum
    else:
        print("Sending packet with corrupted checksum.")
        try:
            packIt.checkSum = hashlib.sha256(str(packIt.message).encode('utf-8')).hexdigest() + "A1B2C3D4E5F6G7H8J9"
        except NameError:
            print("Data in 'message' field is not defined. Failed to calculate checksum.")
            packIt.checkSum = "Undefined"

    packToSend = pickle.dumps(packIt)
    __client.sendall(packToSend)

    return pNum + 1

#Load client settings from settings.json
with open('settings.json') as f:
    json_data = json.load(f)

#INITIAL CLIENT SETTINGS
#Packet info
global packetNum
packetNum = 0
packArray = []
versionNum = json_data["Version"]
encryptMessage = True

global __curChannel, __prevChannel, __prevWhisper

try:
    __client, __username, __curChannel, packetNum = connectToServer(packetNum, versionNum)
except ConnectionRefusedError:
    print("Unable to connect to the server; connection refused.")
    exit()

__prevChannel = __curChannel

print("Type '/help' to view available commands.")

#MAIN CLIENT PROCESS; LISTENING FOR USER INPUT
while True:
    try:
        #https://stackoverflow.com/questions/10829650/delete-the-last-input-row-in-python
        message = input("Enter your message: ")

        #Deletes the previous line so it's easier to read what was said
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")

        #Join a chat channel on the server
        if message[:5].__eq__("/join"):
            channel = message[6:]
            packJoin = packIt(packetNum, versionNum, 11, __curChannel, __username, "", channel, "")
            packArray.append(packJoin)
            packetNum = sendPackIt(packJoin, packetNum, encryptMessage)
            time.sleep(.25)
        #View the channels available on the server
        elif message.__eq__("/channels"):
            packChan = packIt(packetNum, versionNum, 12, __curChannel, __username, "", "(CHANNELS)", "")
            packArray.append(packChan)
            packetNum = sendPackIt(packChan, packetNum, encryptMessage)
            time.sleep(.25)
        #View all users in your current chat channel
        elif message.__eq__("/whochan"):
            packChan = packIt(packetNum, versionNum, 13, __curChannel, __username, "", "(WHOCHAN)", "")
            packArray.append(packChan)
            packetNum = sendPackIt(packChan, packetNum, encryptMessage)
            time.sleep(.25)
        #View all users connected to the server
        elif message.__eq__("/who"):
            packWho = packIt(packetNum, versionNum, 14, __curChannel, __username, "", "(WHO)", "")
            packArray.append(packWho)
            packetNum = sendPackIt(packWho, packetNum, encryptMessage)
            time.sleep(.25)
        #Send a private message to a user on the server
        elif message[:2].__eq__("/w"):
            msg = message.split(' ')
            msgToSend = Fore.MAGENTA + "{0}@{1}=> {2}".format(__username, msg[1], message) + Style.RESET_ALL
            print(msgToSend)
            packWhisp = packIt(packetNum, versionNum, 15, __curChannel, __username, msg[1], msgToSend, "")
            packArray.append(packWhisp)
            packetNum = sendPackIt(packWhisp, packetNum, encryptMessage)
            time.sleep(.25)
        #Reply to the last user who send you a private message
        elif message[:2].__eq__("/r"):
            try:
                msgToSend = Fore.MAGENTA + "{0}@{1}=> {2}".format(__username, __prevWhisper, message) + Style.RESET_ALL
                print(msgToSend)
                packWhisp = packIt(packetNum, versionNum, 15, __curChannel, __username, __prevWhisper, msgToSend, "")
                packArray.append(packWhisp)
                packetNum = sendPackIt(packWhisp, packetNum, encryptMessage)
                time.sleep(.25)
            except NameError:
                print("Error: You have not received a previous whisper from another user.")
        #Lists the available commands
        elif message.__eq__("/help"):
            listCommands()
        #Toggles the encryption on outgoing messages
        elif message.__eq__("/encrypt"):
            if encryptMessage == True:
                encryptMessage = False
                print("Message encryption disabled.")
            else:
                encryptMessage = True
                print("Message encryption enabled.")
        #Disconnects from the server
        elif message.__eq__("/dc"):
            packQuit = packIt(packetNum, versionNum, 99, "", __username, "SERVER", "(DISCONNECT)", "")
            packArray.append(packQuit)
            packetNum = sendPackIt(packQuit, packetNum, encryptMessage)
            __client.close()
        #Connects to the server
        elif message.__eq__("/conn"):
            packetNum = 0
            __client, __username, __curChannel, packetNum = connectToServer(packetNum, versionNum)
            __prevChannel = __curChannel
        #Disconnect from the server, exit the client
        elif message.__eq__("/quit"):
            packQuit = packIt(packetNum, versionNum, 99, "", __username, "SERVER", "(QUIT)", "")
            packArray.append(packQuit)
            packetNum = sendPackIt(packQuit, packetNum, encryptMessage)
            break
        #Send a standard message to the current channel on the server
        else:
            print("{0}@{1}: {2}".format(__username, __curChannel, message))
            packMsg = packIt(packetNum, versionNum, 10, __curChannel, __username, "", message, "")
            packArray.append(packMsg)
            packetNum = sendPackIt(packMsg, packetNum, encryptMessage)

    #Connection lost to server
    except socket.error:
        print("Unable to send message; server connection unavailable.")
        print("Attempting to reconnect to server..")

        #Attempt reconnect to server
        try:
            packetNum = 0
            __client, __username, __curChannel, packetNum = connectToServer(packetNum, versionNum)
            __prevChannel = __curChannel
        except ConnectionRefusedError:
            print("Failed reconnect attempt.")
            
            #Allow user to exit if they cannot reconnect to the server
            message = input("Exit client? (Y|N)")

            if message.upper().__eq__("Y"):
                print("Client exiting..")
                exit()
            continue

        continue
    #Client can still exit with keyboard interrupt
    except (SystemExit, KeyboardInterrupt):
        break

#Proper way to disconnect from the server and close the client
print("Disconnecting..")

try:
    packQuit = packIt(packetNum, versionNum, 99, "", __username, "SERVER", "", "")
    packetNum = sendPackIt(packQuit, packetNum, encryptMessage)
except socket.error:
    pass

time.sleep(.25)
__client.close()
print("Client exiting..")