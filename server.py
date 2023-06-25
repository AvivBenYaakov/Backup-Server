import random
import socket
import string
import sys
import os
import time


def sendCloneFolder(s, path):
    for (root, dirs, files) in os.walk(path, topdown=True):
        s.send(bytes(str.encode('root')))
        data = s.recv(130).decode(encoding)
        if data == 'start':
            bytesRoot = str.encode(root)
            s.send(bytes(bytesRoot))
            data = s.recv(130).decode(encoding)
            if data == 'end':

                s.send(bytes(str.encode('dirs')))
                data = s.recv(130).decode(encoding)
                if data == 'start':
                    for name in dirs:
                        s.send(bytes(str.encode(name)))
                        data = s.recv(130).decode(encoding)
                    s.send(bytes(str.encode('endOfDirName')))
                    data = s.recv(130).decode(encoding)

                s.send(bytes(str.encode('files')))
                data = s.recv(130).decode(encoding)
                if data == 'start':
                    for name in files:
                        s.send(bytes(str.encode(name)))
                        data = s.recv(130).decode(encoding)
                        if not os.stat(root + "/" + name).st_size == 0:
                            s.send(bytes(str.encode("content")))
                            data = s.recv(130).decode(encoding)
                            myfile = open(root + "/" + name, 'rb')
                            s.send(myfile.read())
                        else:
                            s.send(bytes(str.encode("no content")))
                        data = s.recv(130).decode(encoding)
                    s.send(bytes(str.encode('endOfFileName')))
                    data = s.recv(130).decode(encoding)
    s.send(bytes(str.encode('endOfWalk')))


def getCloneFolder(client_socket):
    systemFolder = os.getcwd()
    readable_data = client_socket.recv(100).decode(encoding)
    while readable_data != 'endOfWalk':
        if readable_data == 'root':
            client_socket.send(str.encode('start'))
            rootPath = client_socket.recv(100).decode(encoding)
            if not os.path.exists(rootPath):
                os.mkdir(rootPath)
                newRoot = rootPath
            os.chdir(rootPath)

            client_socket.send(str.encode('end'))
            readable_data = client_socket.recv(100).decode(encoding)
            if readable_data == 'dirs':
                client_socket.send(str.encode('start'))
                dirName = client_socket.recv(100).decode(encoding)
                while dirName != 'endOfDirName':
                    os.mkdir(dirName)
                    client_socket.send(str.encode('continue'))
                    dirName = client_socket.recv(100).decode(encoding)
                client_socket.send(str.encode('end'))
                readable_data = client_socket.recv(100).decode(encoding)

            if readable_data == 'files':
                client_socket.send(str.encode('start'))
                fileName = client_socket.recv(100).decode(encoding)
                while fileName != 'endOfFileName':
                    client_socket.send(str.encode('continue'))
                    isNotEmpty = client_socket.recv(100).decode(encoding)
                    fd = os.open(fileName, os.O_WRONLY | os.O_CREAT)
                    if isNotEmpty == 'content':
                        client_socket.send(str.encode('continue'))
                        content = client_socket.recv(100)
                        os.write(fd, content)
                    os.close(fd)
                    client_socket.send(str.encode('continue'))
                    fileName = client_socket.recv(100).decode(encoding)
                client_socket.send(str.encode('end'))
            os.chdir(systemFolder)
        readable_data = client_socket.recv(100).decode(encoding)
    return newRoot


def createFile(event_path, isDict):
    # TODO: create this file in all the directories of this user
    if not os.path.isdir(event_path):
        fd = os.open(event_path, os.O_WRONLY | os.O_CREAT)
        os.close(fd)

    else:
        os.mkdir(event_path)


def modifyFile(event_path, isDict, content):
    # TODO: modify this file in all the directories of this user

    if not os.path.isdir(event_path):
        fd = os.open(event_path, os.O_WRONLY)
        os.truncate(fd, 0)    #delete content
        os.write(fd, content)
        os.close(fd)


def renameFile(event_path, isDict, dest):
    # TODO: rename this file in all the directories of this user
    os.rename(event_path, dest)


def deleteFile(event_path, isDict):
    if not os.path.isdir(event_path):
        if os.path.exists(event_path):
            # removing the file using the os.remove() method
            os.remove(event_path)
        else:
            # file not found message
            print("File not found in the directory")

    else:
        if os.path.exists(event_path):

            # checking whether the folder is empty or not
            if len(os.listdir(event_path)) == 0:
                # removing the file using the os.remove() method
                os.rmdir(event_path)
            elif event_path != '/':
                for root, dirs, files in os.walk(event_path, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(event_path)
        else:
            # file not found message
            print("File not found in the directory")


def handleEvent(event_path, event_type, isDirectory, dest, content):
    if event_type == "created":
        createFile(event_path, isDirectory)
    if event_type == "modified":
        modifyFile(event_path, isDirectory, content)
    if event_type == "moved":
        renameFile(event_path, isDirectory, dest)
    if event_type == "deleted":
        deleteFile(event_path, isDirectory)


encoding = 'utf-8'
if len(sys.argv) != 2:
    exit(0)
PORT = int(sys.argv[1])
users = {}  # id -> clients
socketList = []   #all clients sockets
clientPath = {}   # id -> rootPath
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', PORT))
server.listen(1)
client_socket = None


while True:
    try:
        server.settimeout(3)
        client_socket, client_address = server.accept()
        if client_socket not in users.values():
            readable_data = client_socket.recv(100).decode(encoding)
            if readable_data == 'newAccount':
                id = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(128))
                print(id + "\n")
                client_socket.send(str.encode(id))
                root = getCloneFolder(client_socket)

                # insert to data structure
                users[id] = []
                users[id].append(client_socket)
                socketList.append(client_socket)
                clientPath[id] = root

            elif readable_data == 'existAccount':
                client_socket.send(str.encode("continue"))
                id = client_socket.recv(130).decode(encoding)
                if id in users:
                    client_socket.send(str.encode("True"))
                    users[id].append(client_socket)  # insert to data structure
                    socketList.append(client_socket)
                    readable_data = client_socket.recv(100).decode(encoding)
                    sendCloneFolder(client_socket, clientPath[id])
    except socket.timeout:
        if client_socket:
            for i in range(0, len(socketList)):

                try:
                    # server's files update
                    socketList[i].settimeout(10)
                    eventPath = socketList[i].recv(100).decode(encoding)
                    socketList[i].send(str.encode("good"))
                    eventType = socketList[i].recv(100).decode(encoding)
                    socketList[i].send(str.encode("good"))
                    isDirectory = socketList[i].recv(100).decode(encoding)
                    socketList[i].send(str.encode("good"))
                    dest = socketList[i].recv(100).decode(encoding)
                    socketList[i].send(str.encode("good"))
                    content = socketList[i].recv(100)
                    socketList[i].send(str.encode("good"))
                    handleEvent(eventPath, eventType, isDirectory, dest, content)

                    # client's files update

                    #find id of client socket
                    for key, value in users.items():
                        for a in range(0, len(value)):
                            if socketList[i] == value[a]:
                                tempId = key
                    # list of all the sockets by id
                    clientList = users[tempId]
                    print(clientList)

                    for j in range(0, len(clientList)):
                        print("before here")
                        if clientList[j] != socketList[i]:
                            print("here")
                            socketList[i].send(str.encode("update"))
                            feedBack = clientList[j].recv(130).decode(encoding)
                            clientList[j].send(str.encode(eventPath))
                            feedBack = clientList[j].recv(130).decode(encoding)
                            clientList[j].send(str.encode(eventType))
                            feedBack = clientList[j].recv(130).decode(encoding)
                            clientList[j].send(str.encode(str(isDirectory)))
                            feedBack = clientList[j].recv(130).decode(encoding)
                            clientList[j].send(str.encode(dest))
                            feedBack = clientList[j].recv(130).decode(encoding)
                            clientList[j].send(content)
                            feedBack = clientList[j].recv(130).decode(encoding)

                except socket.timeout:
                    continue
