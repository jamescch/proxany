from socket import socket, SOCK_STREAM, AF_INET, SOL_SOCKET, SO_REUSEADDR

from decode.tls import parse
from server import create_socket

sock = create_socket('0.0.0.0', 443)

while True:
    (clientsocket, address) = sock.accept()
    parse(clientsocket)
    # ct = client_thread(clientsocket)
    # ct.run()