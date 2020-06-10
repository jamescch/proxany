import threading
import sys
import server

if __name__ == '__main__':

    if not len(sys.argv) == 2:
        print('Usage: python mitm.py <your address> <port>')
    ip = sys.argv[1]
    #ip = '0.0.0.0'
    port = int(sys.argv[2])
    #port = 3128

    threading.Thread(target=server.start, args=(ip, port, 'http')).start()
    threading.Thread(target=server.start, args=(ip, port+1, 'https')).start()
