import select
import socket as Socket
import ssl
import string
import struct
import threading
import time
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
        #return socket.recv(16384)

    def relay(self, proxy_socket, host):
        inputs = [proxy_socket, self.socket]
        outputs = []
        count = 0
        while True:
            # count += 1
            print("select")
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is proxy_socket:
                    raddr = proxy_socket.getsockname()
                    #print '{0} {1} read server'.format(host, raddr[1])
                    #res = self.ReadHttp(s)
                    print("server read")
                    while True:
                        res = self.simple_read(s)
                        print("{}".format(len(res)))

                        if res:
                            #self.print_content(res)
                            print("send to client")
                            #self.socket.sendall(res)
                            wfile = self.socket.makefile('wb')
                            wfile.write(res)
                            wfile.flush()
                            print("pending", proxy_socket.pending())
                            if proxy_socket.pending() == 0:
                                break
                        else:
                            print('server [{} {}] close to client [{}]'.format(host, raddr[1], self.client_port))
                            self.socket.close()
                            proxy_socket.close()
                            return
                else:
                    raddr = s.getpeername()
                    print('client read')
                    #print '{0} {1} read client'.format(host, raddr[1])
                    #res = self.ReadHttp(self.socket)
                    res = self.simple_read(s)
                    if res:
                        wfile = proxy_socket.makefile('w')
                        wfile.write(res.decode())
                        wfile.flush()
                    else:
                        print('server [{} {}] was closed by client [{}]'.format(host, raddr[1], self.client_port))
                        self.socket.close()
                        proxy_socket.close()
                        return

    def send_connect(self, host, proxy, proxy_port, user_agent):
        sock = socket()
        #if self.sslenable == True:
        #    sock = ssl.wrap_socket(sock)
        #addr = Socket.gethostbyname(host)
        print('connect to proxy [{} {}] from client [{}]'.format(proxy, proxy_port, self.socket.getpeername()[1]))
        print('CONNECT {} HTTP/1.1'.format(host))
        print('Host: {}'.format(host))
        print('User-Agent: {}'.format(user_agent))
        print('Proxy-Connection: keep-alive')

        try:
            sock.connect((proxy, proxy_port))
        except OSError as err:
            print('Could not connect to proxy:', err)
            sock.close()
            return None

        sock.sendall('CONNECT {}:443 HTTP/1.1\r\n'.format(host).encode())
        sock.sendall('Host: {}\r\n'.format(host).encode())
        sock.sendall('User-Agent: {}\r\n'.format(user_agent).encode())
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
        print(threading.current_thread().ident, 'run thread')
        # self.retrieve_original_addr(self.socket)
        header, body, user_agent = read_http(self.socket)
        host, port = get_host_from_header(header)
        print('aaa {}:{}'.format(host, port))

        if ("icloud" in host) or ("dropbox" in host) or ("apple" in host):
            return

        if ("wiki" not in host) and ("neverssl" not in host):
            return

        print(header)
        mod_request = header.replace('Connection', 'Proxy-Connection')
        # rsock = self.create_socket_and_connect_to_origin_dst(host, int(port))
        proxy_sock = self.send_connect(host, '192.168.2.1', 3128, user_agent)
        if proxy_sock is None:
            self.socket.close()
            return

        response = read_http(proxy_sock)
        print(response)
        context = ssl.create_default_context()
        proxy_sock = context.wrap_socket(proxy_sock, server_hostname=host)
        # self.socket.sendall((response[0] + response[1]).encode())
        proxy_sock.sendall((mod_request + body).encode())
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
    context.set_servername_callback(sni_callback)
    ssl_socket = context.wrap_socket(server_socket, server_side=True)
    while True:
        client_socket, addr = ssl_socket.accept()
        print(client_socket)
        HttpHandler(client_socket, port).start()


def sni_callback(ssl_socket, server_name, ssl_context):
    print(ssl_socket)
    print(threading.current_thread().ident, "server: ", server_name)
    time.sleep(10)
    return None
