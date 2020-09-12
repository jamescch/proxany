import select
import socket as Socket
import string
import struct
import threading
from socket import *

from httpparser import read_http, get_host_from_header


class HttpHandler(threading.Thread):
    def __init__(self, socket, port):
        threading.Thread.__init__(self)
        self.socket = socket
        if socket:
            self.client_port = socket.getpeername()[1]
        self.listen_port = port

    def create_socket_and_connect_to_origin_dst(self, host, port):
        sock = socket()
        addr = Socket.gethostbyname(host)
        print('connect to server [{} {} {}] from client [{}]'.format(host, addr, port, self.socket.getpeername()[1]))
        sock.connect((addr, port))
        return sock

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

    def redirect_proxy(self, host, proxy, proxy_port):
        sock = socket()
        sock.connect((proxy, proxy_port))

    def retrieve_original_addr(self, socket):
        SO_ORIGINAL_DST = 80
        dst = socket.getsockopt(Socket.SOL_IP, SO_ORIGINAL_DST, 16)
        port, raw_ip = struct.unpack_from("!2xH4s", dst)
        ip = Socket.inet_ntop(Socket.AF_INET, raw_ip)
        print('The original addr is {}:{}'.format(ip, port))

    def run(self):
        # self.retrieve_original_addr(self.socket)
        request = read_http(self.socket)
        host, port = get_host_from_header(request[0])
        print('aaa {}:{}'.format(host, port))

        if ("icloud" in host) or ("dropbox" in host) or ("apple" in host):
            return

        # if ("wiki" not in host) and ("neverssl" not in host):
        #     return

        print(request[0])
        mod_request = request[0]
        # mod_request = request[0].replace('Connection', 'Proxy-Connection')
        mod_request = request[0].replace('GET ', f'GET http://{host}')
        # mod_request = mod_request.replace('\r\n\r\n', '\r\nProxy-Connection: Keep-Alive\r\n\r\n')
        # rsock = self.create_socket_and_connect_to_origin_dst(host, int(port))
        rsock = self.create_socket_and_connect_to_origin_dst('192.168.2.1', 3128)

        # 4. Forward the request sent by user to the fakeSocket
        print(mod_request)
        rsock.sendall((mod_request+request[1]).encode())

        print('Client [{}] Request Forwarding Success'.format(self.client_port))
        # response = self.ReadHttp(rsock)
        # print('Server [{}] responded to client [{}]'.format(host, self.client_port))
        # self.socket.sendall((response[0]+response[1]).encode())
        # print('Server sent')
                
        self.relay(rsock, host)

        # self.socket.close()
        # rsock.close()

        print('Connection Finished')


def start(ip, port):
    bind_address = (ip, port)

    server_socket = socket(AF_INET,SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(bind_address)
    server_socket.listen(1)

    while True:
        client_socket, addr = server_socket.accept()
        HttpHandler(client_socket, port).start()
