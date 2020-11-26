import select
import threading
import socket as Socket
from socket import *

from proxany.decode import tls
from proxany.httpparser import read_http


class HttpsHandler(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        if socket:
            self.client_port = socket.getpeername()[1]

    def create_socket_and_connect_to_origin_dst(self, host, port):
        sock = socket()
        addr = Socket.gethostbyname(host)
        print('connect to server [{} {} {}] from client [{}]'.format(host, addr, port, self.socket.getpeername()[1]))
        sock.connect((addr, port))
        return sock

    def simple_read(self, socket):
        return socket.recv(8192)
        #return socket.recv(16384)

    def relay(self, proxy_socket, host):
        inputs = [proxy_socket, self.socket]
        outputs = []
        while True:
            print("select")
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is proxy_socket:
                    raddr = proxy_socket.getsockname()
                    #print '{0} {1} read server'.format(host, raddr[1])
                    #res = self.ReadHttp(s)
                    print("server read")
                    res = self.simple_read(s)
                    print("{}".format(len(res)))

                    if res:
                        print("send to client")
                        #self.socket.sendall(res)
                        wfile = self.socket.makefile('wb')
                        wfile.write(res)
                        wfile.flush()
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
                        wfile = proxy_socket.makefile('wb')
                        wfile.write(res)
                        wfile.flush()
                    else:
                        print('server [{} {}] was closed by client [{}]'.format(host, raddr[1], self.client_port))
                        self.socket.close()
                        proxy_socket.close()
                        return

    def send_connect(self, server_name, proxy, proxy_port):
        sock = socket()
        print('connect to proxy [{} {}] from client [{}]'.format(proxy, proxy_port, self.socket.getpeername()[1]))
        print('CONNECT {} HTTP/1.1'.format(server_name))
        print('Host: {}'.format(server_name))
        # print('User-Agent: {}'.format(user_agent))
        print('Proxy-Connection: keep-alive')

        try:
            sock.connect((proxy, proxy_port))
        except OSError as err:
            print('Could not connect to proxy:', err)
            sock.close()
            return None

        sock.sendall('CONNECT {}:443 HTTP/1.1\r\n'.format(server_name).encode())
        sock.sendall('Host: {}\r\n'.format(server_name).encode())
        # sock.sendall('User-Agent: {}\r\n'.format(user_agent).encode())
        sock.sendall('Proxy-Connection: keep-alive\r\n\r\n'.encode())

        return sock

    def run(self):
        print(threading.current_thread().ident, 'run thread')
        server_name, data_client_hello = tls.parse(self.socket)

        proxy_sock = self.send_connect(server_name, '192.168.2.1', 3128)
        if proxy_sock is None:
            self.socket.close()
            return

        response = read_http(proxy_sock)
        print('response', response)

        proxy_sock.sendall(data_client_hello)

        self.relay(proxy_sock, server_name)

        print('Connection Finished')