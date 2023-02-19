#coding: utf-8
from socket import *
import sys
import time
#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
serverName = sys.argv[1]

#change this port number if required
serverPort = int(sys.argv[2])

pings = 1

clientSocket = socket(AF_INET, SOCK_DGRAM)
#This line creates the client’s socket. The first parameter indicates the address family;
#  in particular,AF_INET indicates that the underlying network is using IPv4.
# The second parameter indicates that the socket is of type SOCK_DGRAM,which means it is a UDP socket (rather than a TCP socket, where we use SOCK_STREAM).

time_list = []
success_send = 0
fail_send = 0
while pings < 16:

    clientSocket.settimeout(0.6)

    message = 'ping to' + ' ' + '127.0.0.1 ' + 'seq = '+ str(pings)+ ' '
#input() is a built-in function in Python. 
# When this command is executed, the user at the client is prompted with the words “Input lowercase sentence:” 
# The user then uses the keyboard to input a line, which is put into the variable sentence.
#  Now that we have a socket and a message, we will want to send the message through the socket to the destination host.
    start = time.time()
    clientSocket.sendto(message.encode('utf-8'),(serverName, serverPort))
# Note the difference between UDP sendto() and TCP send() calls. In TCP we do not need to attach the destination address to the packet, 
# while in UDP we explicilty specify the destination address + Port No for each message
    try:
        data, server = clientSocket.recvfrom(1024)
        end = time.time()
        elapsed = end - start
        elapsed = int(elapsed*1000)
        time_list.append(elapsed)
        receive_mesg = data.decode('utf-8') + 'RTT = ' + str(elapsed) + 'ms'
        success_send+=1
        print(receive_mesg)
    except timeout:
        fail_send+=1
        receive_mesg = message + 'RTT = ' + 'timeout'
        print (receive_mesg)
    pings = pings + 1
# modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
# Note the difference between UDP recvfrom() and TCP recv() calls.

# print(modifiedMessage.decode('utf-8'))
# # print the received message

clientSocket.close()
# Close the socket

print("--------finish ping----------")
var = '%'
print('Max RTT time = %dms, Min RTT time = %dms, average RTT = %.2lfms, packet lost rate = %.2lf%s' \
    %(max(time_list), min(time_list), sum(time_list)/success_send, \
        (fail_send/(fail_send+success_send)*100),var))
