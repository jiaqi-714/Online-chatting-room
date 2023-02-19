"""
TCP client for comp3331 assignment,use together with TCPServer3.py
"""
from socket import *
import sys
import os
import threading
import time
#Server would be running on the same serverName as Client
serverName = sys.argv[1]
serverPort = int(sys.argv[2])
receiveUDPPort = int(sys.argv[3])
clientClose = False
buf = 1024
def client(clientSocket, receiveUDPPort):
    global clientClose
    global buf
    user_name = ''
    login = False
    start = 0
    ATUclient = []
    clientSocket.sendall(str(receiveUDPPort).encode("utf-8"))
    receiveMasg = clientSocket.recv(2048).decode("utf-8")
    print(receiveMasg,end = '')
    while True:
        if not login:
            if len(receiveMasg.split('!')) >= 1:
                if receiveMasg.split('!')[0] == 'Successful login':
                    login = True
        message = input()
        if start == 0:
            user_name = message
            start = 1
        if message == '':
            if login:
                print('Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):', end = '')
            continue
        command = message.split(' ')[0]
        if command != 'UPD':
            clientSocket.sendall(message.encode("utf-8"))
            receiveMasg = clientSocket.recv(2048).decode("utf-8")
            print(receiveMasg,end = '')
        if command == 'ATU':
            if len(receiveMasg.splitlines()) >= 2:
                ATUclient = receiveMasg.splitlines()
                del ATUclient[-1]
        if command == 'UPD':
            if len(message.split(' ')) >= 3:
                userFound = False
                for user in ATUclient:
                    receiver = message.split(' ')[1]
                    # if this user is online
                    if user.split(', ')[0] == receiver:
                        userFound = True
                        filename = message.split(' ')[2]
                        cur_dir = os.getcwd()
                        file_list = os.listdir(cur_dir)
                        # if file exist in current dictionay
                        if filename in file_list:
                            addr = (user.split(', ')[1], int(user.split(', ')[2]))
                            senderSocket = socket(AF_INET,SOCK_DGRAM)
                            
                            print(f"Sending {filename} to {receiver}...")
                            f=open(filename,"rb")
                            receiveFilename = user_name + '_' + filename
                            senderSocket.sendto(receiveFilename.encode("utf-8"),addr)
                            data = f.read(buf)
                            senderSocket.sendto(data,addr)
                            while True:
                                data = f.read(buf)
                                senderSocket.sendto(data,addr)
                                if not data:
                                    break
                            print(f"Sending {filename} to {receiver} success... please type other command\nEnter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):", end = '')
                            senderSocket.close()
                            f.close()
                            break
                        else:
                            print(f'{filename} is not in this dictionay, please try later\nEnter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):', end = '')
                if not userFound:
                    print(f'{receiver} is not online, please try later\nEnter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):', end = '')
            else:
                print('Invalid number of augument, please type again\nEnter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):', end = '')
        # if receive logout or quit message from server
        if receiveMasg == 'login removed\n' or receiveMasg == '> Invalid Password. Your account has been blocked. Please try again later\n' \
        or receiveMasg == '> Your account is blocked due to multiple login failures. Please try again later\n' or receiveMasg == 'This user Already login, Please logout first\n':
            # Send UDP socket a specfic message to tell it close
            clientClose = True
            senderSocket = socket(AF_INET,SOCK_DGRAM)
            addr = (serverName, receiveUDPPort)
            senderSocket.sendto('Now close the UDP listener'.encode("utf-8"),addr)
            senderSocket.close()
            print(f'Bye, {user_name}')
            break
    clientSocket.close()

def UDPFileReceiver(filename, UDPSocket):
    global buf
    UDPSocket.settimeout(2)
    filename = filename.decode("utf-8")
    sender = filename.split('_')[0]
    print(f"\n{sender} is sending you {filename}...")
    f = open(filename,'wb')
    try:
        data,addr = UDPSocket.recvfrom(buf)
        f.write(data)
    except timeout:
        print('File send broken, please try again\nEnter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):')
        f.close()
        UDPSocket.close()
        return
    while True:
        if not data:
            break
        try:
            data,addr = UDPSocket.recvfrom(buf)
            f.write(data)
        except timeout:
            print('File send broken, please try again')
            f.close()
            UDPSocket.close()
            return
    f.close()
    UDPSocket.close()
    print(f"{filename} success Downloaded from {sender}...\nEnter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD):")




# Tcp client establishment
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))
print(f"Establish the TCP connection to {serverName} {serverPort} success")
client_thread = threading.Thread(target=client, args=(clientSocket,receiveUDPPort))
client_thread.start()

# UDP receiver establishment
while True:
    UDPSocket = socket(AF_INET, SOCK_DGRAM)
    UDPSocket.bind((serverName, receiveUDPPort))
    filename, clientAddress = UDPSocket.recvfrom(1024)
    # receive the specfic quit message and leave
    if filename.decode("utf-8") == 'Now close the UDP listener' and clientClose:
        break
    UDPFilereceive_thread = threading.Thread(target=UDPFileReceiver, args=(filename, UDPSocket))
    UDPFilereceive_thread.start()
    UDPFilereceive_thread.join()
    