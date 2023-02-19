"""
TCP server for comp3331 assignment,use together with TCPClient3.py
"""
from socket import *
import threading
import time
import datetime as dt
from os import path
from datetime import timedelta
import sys

# clear messagelog and userlog
with open("userlog.txt",'w') as f:
    f.truncate(0)
with open("messagelog.txt",'w') as f:
    f.truncate(0)
#Server will run on this port
serverport = int(sys.argv[1])
clients=[]
host = "localhost"
t_lock=threading.Condition()

Max_fail = int(sys.argv[2])
if type(Max_fail) == float or Max_fail > 5 or Max_fail < 1:
    print("Invalid number of allowed failed consecutive attempt: number. The valid value of argument number is an integer between 1 and 5, Set the number of allowed failed consecutive attempt to 3")
    Max_fail = 3
# record the status whether the user is online then it status is true
clients_status = {}
# record the time that the user fail to login
clients_fail_time = {}
# record the time when use can try to login
clients_rework_time = {}
# record ATU status
clients_ATU = {}
client_username = []
cred = open('credentials.txt', 'r')
cred_file = cred.readlines()
cred_list = []
for i in cred_file:
    cred_list.append(i.rstrip())
    client_username.append(i.rstrip().split(' ')[0])
    clients_fail_time[i.rstrip().split(' ')[0]] = 0
    clients_rework_time[i.rstrip().split(' ')[0]] = dt.datetime.now()
    clients_status[i.rstrip().split(' ')[0]] = False
    clients_ATU[i.rstrip().split(' ')[0]] = False
Active_user_seq = 1
mesg_seq = 1


def recv_handler(connectionSocket, ip, clientPort):
    print('Server is ready for service')
    global t_lock
    global Active_user_seq
    global mesg_seq
    fail_login = 0
    login = False
    user_name = '' #who this port sign on
    option_masg = 'Enter one of the following commands (MSG, DLT, EDT, RDM, ATU, OUT, UPD): '
    UDPport, unuseVar1 = connectionSocket.recvfrom(2048)
    UDPport = UDPport.decode('utf-8')
    # print(UDPport)
    loginStatus = 0 #0 means user need type username 1 means user need type Password
    connectionSocket.send('> Username: '.encode('utf-8'))
    while(1):
        clientMessage, unuseVar2 = connectionSocket.recvfrom(2048)
        clientMessage = clientMessage.decode('utf-8')
        if loginStatus == 0: 
            serverMessage = '> Username: '
        elif loginStatus == 1: 
            serverMessage = '> Password: '
        elif loginStatus == 2 and login:
            serverMessage = 'Invalid input, please type one of this command\n'+option_masg
        currtime = dt.datetime.now()
        date_time = currtime.strftime("%d %b %Y %H:%M:%S")
        outPutMessage = f'Received request from {user_name} {ip} {clientPort} at time {date_time}'
        #get lock as we might me accessing some shared data structures
        with t_lock:
            currtime = dt.datetime.now()
            date_time = currtime.strftime("%d %b %Y %H:%M:%S")
            # get which command from user
            if clientMessage == '':
                command = 'EMPTY'
            else:
                command = clientMessage.split(' ')[0] 
            # used for user login
            if not login:
                if loginStatus == 1:
                    loginPassword = clientMessage
                    loginStatus +=1
                if loginStatus == 0:
                    clientname = clientMessage
                    user_name = clientname
                    loginStatus +=1
                    serverMessage = '> Password: '
                if loginStatus == 2:
                    # if this user is not banned
                    if clients_rework_time[clientname] < currtime:
                        # if user already login
                        if clients_status[clientname]:
                            serverMessage = f'This user Already login, Please logout first\n'
                            connectionSocket.send(serverMessage.encode('utf-8'))
                            t_lock.notify()
                            break
                        # if user not login
                        else:
                            username_password = clientname + ' ' + loginPassword
                            # if user's username and password is correct
                            if username_password in cred_list:
                                #store client information (IP and Port No) in list
                                user_name = clientname
                                serverMessage = 'Successful login! This is option:\n'+option_masg
                                outPutMessage = f'{user_name} login at {date_time}'
                                userlog_masg = str(Active_user_seq)+'; ' + date_time+ '; '+clientname + '; ' + ip + '; ' + UDPport + '\n'
                                userlog_file = open("userlog.txt","a+")
                                userlog_file.write(userlog_masg)
                                userlog_file.close()
                                clients_fail_time[clientname] = 0
                                Active_user_seq += 1
                                clients_status[clientname] = True
                                login = True
                                loginStatus = 2
                            # if username and password is not correct
                            else:
                                serverMessage = 'Invalid password\n> Password: '
                                outPutMessage = f'{user_name} type wrong password at {date_time}'
                                clients_fail_time[clientname] += 1
                                loginStatus = 1
                                # if username type wrong password too many times
                                if clients_fail_time[clientname] >= Max_fail:
                                    clients_rework_time[clientname] = currtime + timedelta(seconds=10)
                                    clients_fail_time[clientname] = 0
                                    connectionSocket.send("> Invalid Password. Your account has been blocked. Please try again later\n".encode('utf-8'))
                                    t_lock.notify()
                                    break
                    # if username is blocked and user still want login
                    else:
                        serverMessage = '> Your account is blocked due to multiple login failures. Please try again later\n'
                        outPutMessage = f'{user_name} try to login to a blocked account at {date_time}'
                        connectionSocket.send(serverMessage.encode('utf-8'))
                        t_lock.notify()
                        break
            # this is for user to logout
            if command == 'OUT' or command == 'quit':
                if login and clientMessage == 'OUT':
                    clients_status[user_name] = False
                    clients_ATU[user_name] = False
                    with open("userlog.txt") as f:
                        content = f.readlines()
                        #remove whitespace characters like `\n` at the end of each line
                        content = [x.strip() for x in content]
                        for line in content:
                            loginUser = line.split('; ')[2]
                            if loginUser == user_name:
                                deleteUserlog = line
                    with open("userlog.txt", 'w') as f:
                        newUserSeq = 1
                        for line in content:
                            if line.strip("\n") != deleteUserlog:
                                newUserlog = line.split('; ')
                                # change the message seq
                                del newUserlog[0]
                                newUserlog = '; '.join(newUserlog)
                                f.write(f'{newUserSeq}; {newUserlog}\n')
                                newUserSeq +=1
                        Active_user_seq = newUserSeq        
                    connectionSocket.send(f"login removed\n".encode('utf-8'))
                    print(f'{user_name} logout at {date_time}')
                    t_lock.notify()
                    break
                # this is for user to quit when this user have not login
                elif clientMessage == 'quit':
                    connectionSocket.send("login removed\n".encode('utf-8'))
                    print(f'{ip} {clientPort} cancel login at {date_time}')
                    t_lock.notify()
                    break
            # this is for user send MSG command
            if command == 'MSG' and login:
                if len(clientMessage.split(' ')) > 1:
                    mesgContent = clientMessage.split(' ')
                    mesgContent.remove('MSG')
                    mesgContent = ' '.join(mesgContent)
                    messagelog_file = open("messagelog.txt","a+")
                    messagelog_file.write(str(mesg_seq)+'; ' + date_time+ '; '+user_name + '; ' + mesgContent + '; '+ 'no\n')
                    messagelog_file.close()
                    serverMessage = f'Success send #{mesg_seq:}"{mesgContent}" at {date_time}\n{option_masg}'
                    outPutMessage = f'{user_name} Success send #{mesg_seq:}"{mesgContent}" at {date_time}'
                    mesg_seq += 1
                else:
                    serverMessage = 'invalid number of augument, please type again\n' + option_masg
            # this is for user to delete or edit message
            if command == 'DLT' or command == 'EDT':
                if login:
                    if len(clientMessage.split(' ')) >= 3:
                        masgFind = False
                        inputTime = clientMessage.split(' ')
                        del inputTime[0]
                        del inputTime[0]
                        while len(inputTime) > 4:
                            del inputTime[4]
                        # get actual timestamp from input
                        inputTime = ' '.join(inputTime)
                        with open("messagelog.txt") as f:
                            content = f.readlines()
                            #remove whitespace characters like `\n` at the end of each line
                            content = [x.strip() for x in content] 
                            for line in content:
                                messageId = line.split('; ')[0]
                                postTime = line.split('; ')[1]
                                postUser = line.split('; ')[2]
                                inputId = clientMessage.split(' ')[1]
                                inputId = inputId[1:]
                                if postUser == user_name and messageId == inputId and inputTime == postTime:
                                    deleteMessage = line
                                    deleteMessageId = deleteMessage.split('; ')[0]
                                    deleteMessageContent = deleteMessage.split('; ')[3]
                                    masgFind = True
                                else:
                                    outPutMessage = f'{user_name} attempt to edit message #{inputId} at {date_time}, Authorisation fails.'
                                    serverMessage = f'The informatiom you type were not correspond to valid message or you cannot change this message\n{option_masg}'
                        # if find this message
                        if masgFind and command == 'DLT':
                            with open("messagelog.txt", 'w') as f:
                                newMasgSeq = 1
                                for line in content:
                                    if line.strip("\n") != deleteMessage:
                                        newMesg = line.split('; ')
                                        # change the message seq
                                        del newMesg[0]
                                        newMesg = '; '.join(newMesg)
                                        f.write(f'{newMasgSeq}; {newMesg}\n')
                                        newMasgSeq +=1
                                mesg_seq = newMasgSeq
                            outPutMessage = f'{user_name} Success delete message {deleteMessageId}: "{deleteMessageContent} at {date_time}'
                            serverMessage = f'Success delete message {deleteMessageId}: "{deleteMessageContent}"\n{option_masg}'
                        # if find this message
                        if masgFind and command == 'EDT':
                            newMesgContent = clientMessage.split(' ')
                            # get new message content
                            for _ in range(0,6):
                                del newMesgContent[0]
                            newMesgContent = ' '.join(newMesgContent)
                            with open("messagelog.txt", 'w') as f:
                                for line in content:
                                    if line.strip("\n") == deleteMessage:
                                        newMesg = line.split('; ')
                                        newMesg[1] = date_time
                                        newMesg[3] = newMesgContent
                                        newMesg[4] = 'yes'
                                        newMesg = '; '.join(newMesg)
                                        f.write(f'{newMesg}\n')
                                    else:
                                        f.write(line+'\n')
                            outPutMessage = f'{user_name} Success edit message {deleteMessageId}: "{deleteMessageContent}" to "{newMesgContent}" at {date_time}'
                            serverMessage = f'Success edit message {deleteMessageId}: "{deleteMessageContent}" to "{newMesgContent}"\n{option_masg}'   
                    else:
                        serverMessage = 'Invalid number of augument, please type again\n' + option_masg
            # This is for user to read message
            if command == 'RDM' and login:
                inputTime = clientMessage.split(' ')
                del inputTime[0]
                inputTime = ' '.join(inputTime)
                returnMasg = ''
                with open("messagelog.txt") as f:
                    content = f.readlines()
                    for line in content:
                        postTime = line.split('; ')[1]
                        postSeq = line.split('; ')[0]
                        postUser = line.split('; ')[2]
                        postCont = line.split('; ')[3]
                        edited = line.split('; ')[4].strip()
                        if edited == 'yes':
                            postType = 'edited'
                        else:
                            postType = 'posted'
                        if postTime > inputTime:
                            thisline = f'#{postSeq}; {postUser}: "{postCont}" {postType} at {postTime}\n'
                            returnMasg = returnMasg + thisline
                if returnMasg == '':
                    outPutMessage = f'{user_name} issue RDM command at {date_time}, No new message'
                    serverMessage = f'no new message, please type other command\n{option_masg}'
                else:
                    serverMessage = returnMasg + option_masg
                    outPutMessage = f'{user_name} issue RDM command at {date_time}, return\n{returnMasg.strip()}'
            # this is for user to use ATU command
            if command == 'ATU' and login:
                clients_ATU[user_name] = True
                returnMasg = ''
                for user,value in clients_ATU.items():
                    if value == True and user != user_name and clients_status[user] == True:
                        with open("userlog.txt") as f:
                            content = f.readlines()
                            #remove whitespace characters like `\n` at the end of each line
                            content = [x.strip() for x in content] 
                            for line in content:
                                if line.split('; ')[2] == user:
                                    newMesg = line.split('; ')
                                    # change the message seq
                                    del newMesg[0]
                                    newMesg = f'{(newMesg)[1]}, {newMesg[2]}, {newMesg[3].strip()}, is active since {(newMesg)[0]}'
                                    returnMasg = returnMasg + newMesg+'\n'
                if returnMasg == '':
                    serverMessage = f'No other active user, pleast type other command{option_masg}'
                    outPutMessage = f'{user_name} issue RDM command at {date_time}, No other active user'
                else:
                    serverMessage = f'{returnMasg.strip()}\n{option_masg}'
                    outPutMessage = f'{user_name} issue RDM command at {date_time}, return\n{returnMasg.strip()}'

            #send message to the client
            connectionSocket.send(serverMessage.encode('utf-8'))
            print(outPutMessage)
            t_lock.notify()
    

    print(f'TCP Connectionclose with {user_name} {ip} {clientPort}')
    connectionSocket.close()

# Set TCP socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
print("Socket created")
try:
    serverSocket.bind((host, serverport))
except:
    print("Bind failed. Error : " + str(sys.exc_info()))
    sys.exit()
serverSocket.listen(1) 
print("Socket now listening")
# infinite loop- do not reset for every requests
while True:
    connectionSocket, clientaddress = serverSocket.accept()
    ip, clientPort = str(clientaddress[0]), str(clientaddress[1])
    print("Connected with " + ip + ":" + clientPort)
    try:
        # create new thread for new client
        clientThread = threading.Thread(target=recv_handler, args=(connectionSocket, ip, clientPort))
        clientThread.start()
    except:
        print("Thread did not start.")

serverSocket.close()

