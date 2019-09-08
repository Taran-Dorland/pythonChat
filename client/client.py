import socket
import threading
import time
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
            print("Server connection error.\n")
            break

#Outputs a list of commands that the user can exnter in the chat
def listCommands():
    print("List of commands: ")
    print("/who\t\t:Lists current users connected to the server.")
    print('/channels\t:Returns a list of channels on the server.')
    print("/join 'channel'\t:User joins the specified channel.")
    print("/part 'channel'\t:User parts the specified channel.")
    print("/conn\t\t:Connects to the server.")
    print("/dc\t\t:Disconnects from the server.")
    print("/quit\t\t:Disconnects from the server and exits the program.\n")

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
                print("Name already in use.")
            else:
                print(data)
                channel = conn.recv(1024).decode('utf-8')
                return username, channel

        except socket.error:
            print("Error connecting to server.")
            exit()

#For auto-login
def autoUsername(conn, username):
    while True:
        try:
            conn.sendall(username.encode('utf-8'))

            reply = conn.recv(1024)
            data = reply.decode('utf-8')

            if data.__eq__("0"):
                print("Name already in use.")
            else:
                print(data)
                channel = conn.recv(1024).decode('utf-8')
                return username, channel

        except socket.error:
            print("Error connecting to server.")
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

    reply = __client.recv(1024).decode('utf-8')
    if reply.__eq__("155"):
        __curChannel = __curChannel
    else:
        __curChannel = channel[4:]

#Load client settings from settings.json
with open('C:\GitProjects\pythonchat\client\settings.json') as f:
    json_data = json.load(f)

__client, __username, __curChannel = connectToServer()

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
            listCommands()
        elif message.__eq__("/dc"):
            __client.close()
        elif message.__eq__("/conn"):
            __client = connectToServer()
        elif message[:5].__eq__("/join"):
            switchChannel(message)
        else:
            print("{0}@{1}: {2}".format(__username, __curChannel, message))
            __client.sendall(message.encode('utf-8'))

    except (SystemExit, KeyboardInterrupt):
        break