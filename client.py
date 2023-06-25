import socket
import sys
import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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


class MyHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        s.send(str.encode(event.src_path))
        data = s.recv(130).decode(encoding)
        s.send(str.encode(event.event_type))
        data = s.recv(130).decode(encoding)
        s.send(str.encode(str(event.is_directory)))
        data = s.recv(130).decode(encoding)
        dest = 'temp'
        if event.event_type == "moved":
            dest = event.dest_path
        s.send(str.encode(dest))
        data = s.recv(130).decode(encoding)
        content = str.encode('temp')
        if event.event_type == "modified" and not os.path.isdir(event.src_path):
            myfile = open(event.src_path, 'rb')
            content = myfile.read()
        s.send(content)
        data = s.recv(130).decode(encoding)


class PausingObserver(Observer):
    def dispatch_events(self, *args, **kwargs):
        if not getattr(self, '_is_paused', False):
            super(PausingObserver, self).dispatch_events(*args, **kwargs)

    def pause(self):
        self._is_paused = True

    def resume(self):
        time.sleep(10)  # allow interim events to be queued
        self.event_queue.queue.clear()
        self._is_paused = False

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
            os.chdir(systemFolder)
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


encoding = 'utf-8'
argSize = len(sys.argv)
isRegister = (argSize == 6)  # true - size is 5, false size is 4
if (argSize < 5) or (argSize > 6):
    exit(0)
ip = sys.argv[1]
port = int(sys.argv[2])
path = sys.argv[3]
waitTime = sys.argv[4]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, port))
if isRegister:
    identifier = sys.argv[5]
    s.send(bytes(str.encode('existAccount')))
    readable_data = s.recv(130).decode(encoding)

    s.send(bytes(str.encode(identifier)))
    check = s.recv(130).decode(encoding)

    # check if identifier existed in the server
    if check == 'True':
        s.send(bytes(str.encode('continue')))
        path = getCloneFolder(s)

else:
    s.send(bytes(str.encode('newAccount')))
    identifier = s.recv(130).decode(encoding)
    sendCloneFolder(s, path)


my_event_handler = MyHandler()
my_observer = PausingObserver()
my_observer.schedule(my_event_handler, path, recursive=True)
my_observer.start()

try:
    while True:
        time.sleep(float(waitTime))
        message = s.recv(130).decode(encoding)
        if message == "update":
            #my_observer.pause()
            s.send(str.encode("good"))
            eventPath = s.recv(100).decode(encoding)
            s.send(str.encode("good"))
            eventType = s.recv(100).decode(encoding)
            s.send(str.encode("good"))
            isDirectory = s.recv(100).decode(encoding)
            s.send(str.encode("good"))
            dest = s.recv(100).decode(encoding)
            s.send(str.encode("good"))
            content = s.recv(100)
            s.send(str.encode("good"))
            handleEvent(eventPath, eventType, isDirectory, dest, content)
            #my_observer.resume()

except KeyboardInterrupt:
    my_observer.stop()
my_observer.join()


