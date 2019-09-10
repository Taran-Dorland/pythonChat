import socket
import threading
import time
import json

#https://pypi.org/project/colorama/
from colorama import init, Fore, Back, Style

#Listens for incoming data from server
def incoming(conn):

    global __curChannel, __prevChannel, __prevWhisper

    while True:
        try:
            message = conn.recv(1024).decode('utf-8')

            #Error 155: Failed to swap channel
            #1: Success
            #10: Private message
            if message.__eq__("155"):
                __curChannel = __prevChannel
            elif message.__eq__("1"):
                time.sleep(.1)
            elif message[:2].__eq__("10"):
                print(Fore.MAGENTA + message[2:] + Style.RESET_ALL)
                user = message.split('@')
                __prevWhisper = user[0][2:]
            else:
                print(message)

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

#Sends a message to the server to switch chat channel
def switchChannel(message):
    channel = "join" + message[6:]
    __client.sendall(channel.encode('utf-8'))

    return message[6:]

#Load client settings from settings.json
with open('D:\Git Projects\pythonChat\client\settings.json') as f:
    json_data = json.load(f)

global __curChannel, __prevChannel, __prevWhisper
__client, __username, __curChannel = connectToServer()
__prevChannel = __curChannel

#Client main
while True:
    try:
        #https://stackoverflow.com/questions/10829650/delete-the-last-input-row-in-python
        message = input("Enter your message: ")
        print("\033[A                             \033[A")

        #Kill connection to server and terminate program
        if message.__eq__("/quit"):
            __client.close()
            exit()
        elif message.__eq__("/help"):
            print(message)
            listCommands()
        elif message.__eq__("/dc"):
            print(message)
            __client.close()
        elif message.__eq__("/conn"):
            print(message)
            __client = connectToServer()
        elif message[:5].__eq__("/join"):
            print(message)
            __prevChannel = __curChannel
            __curChannel = switchChannel(message)
            time.sleep(.25)
        elif message.__eq__("/channels"):
            print(message)
            __client.sendall("chan".encode('utf-8'))
            time.sleep(.25)
        elif message.__eq__("/whochan"):
            command = "whochan_" + __curChannel
            __client.sendall(command.encode('utf-8'))
            time.sleep(.25)
        elif message.__eq__("/who"):
            __client.sendall("who".encode('utf-8'))
            time.sleep(.25)
        elif message[:2].__eq__("/w"):
            cmdMsg = message.split(' ')
            fixMsg = "".join(str(e + " ") for e in cmdMsg)
            #cmdMsg[1] == user to send message to
            command = "w_" + cmdMsg[1] + "_" + fixMsg
            print(Fore.MAGENTA + "{0}@{1}=> {2}".format(__username, cmdMsg[1], fixMsg) + Style.RESET_ALL)
            __client.sendall(command.encode('utf-8'))
            time.sleep(.25)
        elif message[:2].__eq__("/r"):
            command = "w_" + __prevWhisper + "_" + message
            print(Fore.MAGENTA + "{0}@{1}=> {2}".format(__username, __prevWhisper, message) + Style.RESET_ALL)
            __client.sendall(command.encode('utf-8'))
            time.sleep(.25)
        else:
            print("{0}@{1}: {2}".format(__username, __curChannel, message))
            __client.sendall(message.encode('utf-8'))

    except (SystemExit, KeyboardInterrupt):
        break