import re


def read_http(sock):
    # Read whole Http packet, and return header and body in string type
    #dic_header, header = self.read_header(source_sock)
    res = read_header(sock)

    if not res:
        return

    dic_header = res[0]
    header = res[1]

    user_agent = None
    if 'User-Agent' in dic_header:
        user_agent = dic_header['User-Agent']

    body = ""
    if 'Transfer-Encoding' in dic_header and dic_header['Transfer-Encoding'] == 'chunked':
        line = read_line(sock)
        body += line
        chunk_size = int(line,16)
        print('chunk size is {}'.format(chunk_size))
        #while True :

        if chunk_size != 0 :
            line = read_num(sock, chunk_size+2)
            body += line

    else:
        if 'Content-Length' in dic_header:
            length = int(dic_header['Content-Length'])
        else:
            length = 0

        while length > 0:
            line = sock.recv(1)
            length -= len(line)
            body += line

        #self.PrinfContent(body)
    return header, body, user_agent


def get_host_from_header(header):
    # Parsing first http packet and find
    # 1) if ssl enable, if header contain "CONNECT 192.168.6.131:443 HTTP/1.1"
    #   then it is https connection, and port and host are return
    # 2) port need to connect
    # 3) host need to conect

    ssl_enable = False
    if 'CONNECT' in header:
        ssl_enable = True

    #print "The header is: "+header
    m_host = re.search('Host: (.*)\r\n', header)
    host = m_host.group(1)
    #tokens = str(header).split('\r\n')
    #tokens = tokens[1].split(' ')
    #host = tokens[1]

    if ssl_enable:
        port = 443
    else:
        port = 80

    return host, port


def read_header(sock):
    #This function read the http header from socket
    header = ""
    line = sock.recv(1)

    data = line
    while len(line) :
        line = sock.recv(1)
        data += line
        if data.find(b'\r\n\r\n') != -1 :
            header = data
            data = ""
            break
    str_header = header.decode()
    dic_header = dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", str_header))
    #print dic_header
    #for (k,v) in dic_header.items():
    #        print k,":",v
    return dic_header, str_header


def read_line(sock):
    # This function read a line from socket
    line = ""
    while True:
        char = sock.recv(1)
        line += char
        if not line.find("\r\n") == -1 :
            return line


def read_num(sock, length):
    # read data with lenth from source_sock
    line = ""
    while len(line) < length:
        char = sock.recv(1)
        line += char
    return line
