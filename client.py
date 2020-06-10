from socket import *
import ssl
import time
import re
import struct
import string
import os
import sys
import socket as Socket

s = socket(AF_INET, SOCK_STREAM)
s.connect(("127.0.0.1", 443))
context = ssl.create_default_context()
context.wrap_socket(s, server_hostname='127.0.0.1')


s.sendall(b'aaaaa')

i = 1
while True:
    res = s.recv(5)
    if res == b'':
        break
    print('{} receive: {}'.format(i, res.decode()))
    i += 1