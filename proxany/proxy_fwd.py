import threading
import sys

sys.path += ['../proximate']
print(sys.path)
from proxany import server


if __name__ == '__main__':

    if not len(sys.argv) == 3:
        print(f'Usage: python {sys.argv[0]} <your address> <port>')
        exit(1)
    ip = sys.argv[1]
    # ip = '0.0.0.0'
    port = int(sys.argv[2])
    # port = 3128

    # server.start(ip, port, 'http')
    threading.Thread(target=server.start, args=(ip, port, 'http')).start()
    threading.Thread(target=server.start, args=(ip, port + 1, 'https')).start()
