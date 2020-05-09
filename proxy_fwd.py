import threading
import sys
import http_proxy_fwd
import https_proxy_fwd

if __name__ == '__main__':

    if not len(sys.argv) == 2 :
        print('Usage: python mitm.py <your address> <port>')
    ip = sys.argv[1]
    #ip = '0.0.0.0'
    port = int(sys.argv[2])
    #port = 3128

    threading.Thread(target=http_proxy_fwd.start, args=(ip, port)).start()
    threading.Thread(target=https_proxy_fwd.start, args=(ip, port+1)).start()
