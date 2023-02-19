# Sample code for Multi-Threaded Server
#Python 3
# Usage: python3 UDPserver3.py
#coding: utf-8
from socket import *
import threading
import time
import datetime as dt

from datetime import timedelta
import sys

#Server will run on this port
serverPort = 12000
t_lock=threading.Condition()
#will store clients info in this list
clients=[]
# would communicate with clients after every second
UPDATE_INTERVAL= 1
timeout=False
Max_fail = int(sys.argv[1])

if type(Max_fail) == float or Max_fail > 5 or Max_fail < 1:
    print("Invalid number of allowed failed consecutive attempt: number. The valid value of argument number is an integer between 1 and 5, Set the number of allowed failed consecutive attempt to 3")
    Max_fail = 3
clients_status = {}
clients_fail_time = {}
clients_rework_time = {}
cred = open('credentials.txt', 'r')
cred_file = cred.readlines()
cred_list = []
for i in cred_file:
    cred_list.append(i.rstrip())
    clients_fail_time[i.rstrip().split(' ')[0]] = 0
    clients_rework_time[i.rstrip().split(' ')[0]] = dt.datetime.now()
    clients_status[i.rstrip().split(' ')[0]] = False
Active_user_seq = 1


# for i,k in clients_rework_time.items():
#     print(k)
print(clients_fail_time)
def recv_handler():
    global t_lock
    global clients
    global clientSocket
    global serverSocket
    global cred_list
    global Active_user_seq
    fail_login = 0
    time_to_rework = dt.datetime.now()
    login = False
    option_masg = ' MSG: Post Message\n DLT: Delete Message\n EDT: Edit Message\n RDM: Read Message\n ATU: Display active users\n OUT: Log out and UPD: Upload file'

    print('Server is ready for service')
    while(1):
        message, clientAddress = serverSocket.recvfrom(2048)
        # print(clientAddress)
        #received data from the client, now we know who we are talking with
        message = message.decode()
        #get lock as we might me accessing some shared data structures
        with t_lock:
            currtime = dt.datetime.now()
            date_time = currtime.strftime("%d/%m/%Y, %H:%M:%S")
            print('Received request from', clientAddress[0], 'listening at', clientAddress[1], ':', message, 'at time ', date_time)
            if not login: 
                serverMessage = 'Please login. login format "login username password'
            else:
                serverMessage = option_masg
            # get which command from user
            command = message.split(' ')[0]

            if command == 'login':
                clientname = message.split(' ')[1]
                if clients_fail_time[clientname] >= Max_fail:
                    clients_rework_time[clientname] = currtime + timedelta(seconds=10)
                    clients_fail_time[clientname] = 0
                
                # if this user is not banned
                if clients_rework_time[clientname] < currtime:
                    if clients_status[clientname]:
                        serverMessage = 'This user Already login, Please type other command'
                        print(clientAddress)
                    else:
                        username_password = clientname + ' ' + message.split(' ')[2]
                        if username_password in cred_list:
                            #store client information (IP and Port No) in list
                            clients.append(clientAddress)
                            serverMessage = 'Successful login! This is option:\n'+option_masg
                            userlog_masg = str(Active_user_seq)+'; ' + date_time+ '; '+clientname + '; ' + str(clientAddress[0])+ '; ' + str(clientAddress[1]) + '\n'
                            userlog_file = open("userlog.txt","a+")
                            userlog_file.write(userlog_masg)
                            userlog_file.close()
                            clients_fail_time[clientname] = 0
                            Active_user_seq += 1
                            clients_status[clientname] = True
                            login = True
                        else:
                            serverMessage = 'Invalid username or password'
                            clients_fail_time[clientname] += 1
                else:
                    remain = clients_rework_time[clientname] - currtime
                    serverMessage = f'Please wait for seconds, remain time = {round(remain.total_seconds(),2)}'
            if clientAddress in clients:
                if(command=='logout'):
                    #check if client already subscribed or not
                    if(clientAddress in clients):
                        clients.remove(clientAddress)
                        serverMessage="login removed"
                        clients_status[clientname] = False
            #send message to the client
            serverSocket.sendto(serverMessage.encode(), clientAddress)
            #notify the thread waiting
            t_lock.notify()


def send_handler():
    global t_lock
    global clients
    global clientSocket
    global serverSocket
    global timeout
    #go through the list of the subscribed clients and send them the current time after every 1 second
    while(1):
        #get lock
        with t_lock:
            # for i in clients:
                # currtime =dt.datetime.now()
                # date_time = currtime.strftime("%d/%m/%Y, %H:%M:%S")
                # message='Current time is ' + date_time
                # clientSocket.sendto(message.encode(), i)
                # print('Sending time to', i[0], 'listening at', i[1], 'at time ', date_time)
            #notify other thread
            t_lock.notify()
        #sleep for UPDATE_INTERVAL
        time.sleep(UPDATE_INTERVAL)

#we will use two sockets, one for sending and one for receiving
clientSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('localhost', serverPort))

recv_thread=threading.Thread(name="RecvHandler", target=recv_handler)
recv_thread.daemon=True
recv_thread.start()

send_thread=threading.Thread(name="SendHandler",target=send_handler)
send_thread.daemon=True
send_thread.start()
#this is the main thread
while True:
    time.sleep(0.1)

def client_login(message):
    if command == 'login':
        clientname = message.split(' ')[1]
        if clients_fail_time[clientname] >= Max_fail:
            clients_rework_time[clientname] = currtime + timedelta(seconds=10)
            clients_fail_time[clientname] = 0
        
        # if this user is not banned
        if clients_rework_time[clientname] < currtime:
            if clients_status[clientname]:
                serverMessage = 'This user Already login, Please type other command'
                print(clientAddress)
            else:
                username_password = clientname + ' ' + message.split(' ')[2]
                if username_password in cred_list:
                    #store client information (IP and Port No) in list
                    clients.append(clientAddress)
                    serverMessage = 'Successful login! This is option:\n'+option_masg
                    userlog_masg = str(Active_user_seq)+'; ' + date_time+ '; '+clientname + '; ' + str(clientAddress[0])+ '; ' + str(clientAddress[1]) + '\n'
                    userlog_file = open("userlog.txt","a+")
                    userlog_file.write(userlog_masg)
                    userlog_file.close()
                    clients_fail_time[clientname] = 0
                    Active_user_seq += 1
                    clients_status[clientname] = True
                    login = True
                else:
                    serverMessage = 'Invalid username or password'
                    clients_fail_time[clientname] += 1
        else:
            remain = clients_rework_time[clientname] - currtime
            serverMessage = f'Please wait for seconds, remain time = {round(remain.total_seconds(),2)}'
    if clientAddress in clients:
        if(command=='logout'):
            #check if client already subscribed or not
            if(clientAddress in clients):
                clients.remove(clientAddress)
                serverMessage="login removed"
                clients_status[clientname] = False