import threading
import sys

sys.path += ['../proximate']
print(sys.path)
from proxany import server


if __name__ == '__main__':

    if not len(sys.argv) == 5:
        print(f'Usage: python {sys.argv[0]} <your address> <port> <proxy ip> <proxy port>')
        exit(1)
    ip = sys.argv[1]
    # ip = '0.0.0.0'
    port = int(sys.argv[2])
    # port = 3128
    proxy_ip = sys.argv[3]
    proxy_port = sys.argv[4]

    # server.start(ip, port, 'http')
    threading.Thread(target=server.start, args=(ip, port, 'http', proxy_ip, proxy_port)).start()
    threading.Thread(target=server.start, args=(ip, port + 1, 'https', proxy_ip, proxy_port)).start()
