from proxany.decode.tls import parse
from proxany.server import create_socket

sock = create_socket('0.0.0.0', 443)

while True:
    (clientsocket, address) = sock.accept()
    parse(clientsocket)
    # ct = client_thread(clientsocket)
    # ct.run()