from socket import *
import threading
import time
import ssl

from proxany.handler.https import HttpsHandler
from proxany.http_proxy_fwd import HttpHandler


class client_thread(threading.Thread):
    
    def __init__(self, socket) :
        threading.Thread.__init__(self)
        self.socket = socket
        if socket:
            self.client_port = socket.getpeername()[1]

    def run(self):
        chunk = self.socket.recv(5)
        print('receive from client: {}'.format(chunk.decode()))

        s = None
        for i in range(5000):
            s += 'f'

        for i in range(1000):
            self.socket.sendall(s.encode())
            time.sleep(0.01)
        self.socket.close()


def create_socket(ip, port):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)    
    server_socket.bind((ip, port))
    server_socket.listen(1)
    return server_socket


def create_tls_intercept_socket(socket_obj):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('myCA.pem', 'myCA.pem')
    ssl_socket = context.wrap_socket(socket_obj, server_side=True)
    return ssl_socket


def create_tls_socket(socket_obj):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # context.load_cert_chain('myCA.pem', 'myCA.pem')
    context.set_servername_callback(sni_callback)
    ssl_socket = context.wrap_socket(socket_obj, server_side=True, do_handshake_on_connect=True)
    return ssl_socket


def sni_callback(ssl_socket, server_name, ssl_context):
    print(ssl_socket)
    print(threading.current_thread().ident, "server: ", server_name)
    time.sleep(10)
    HttpsHandler(ssl_socket, None).start()
    return None


def start(ip, port, mode, proxy_ip, proxy_port):
    if mode is 'http':
        socket_obj = create_socket(ip, port)
        while True:
            client_socket, address = socket_obj.accept()
            ct = HttpHandler(client_socket, proxy_ip, proxy_port)
            print('connect start')
            ct.start()
            print('connect fin')
    elif mode is 'https':
        socket_obj = create_socket(ip, port)
        # socket_obj = create_tls_socket(socket_obj)
        while True:
            client_socket, address = socket_obj.accept()
            ct = HttpsHandler(client_socket, proxy_ip, proxy_port)
            ct.start()
            print(threading.current_thread().ident, 'accept')
