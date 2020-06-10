import socket

PROTOCOL = 0
HEADER = 1
PAYLOAD = 2
HANDSHAKE = 3
EXTENSION = 4
SERVER_NAME = 5
ERROR = 10


def parse(skt):
    state = HEADER
    num_to_read = 5
    data = b''
    index = 0
    while True:
        if state == HEADER:
            # 5 byte
            r = skt.recv(num_to_read)
            print(r[:2])
            if r[:1] == b'\x16':
                print("Content Type: HandShake")
            else:
                state = ERROR
                continue
            print("Version: 1.{}".format(int.from_bytes(r[2:3], 'big') - 1))

            print(r[3:5].hex())
            length = int.from_bytes(r[3:5], byteorder='big')
            print("Length: {}".format(length))

            num_to_read = length
            state = PAYLOAD
            data += r
        elif state == PAYLOAD:
            print('read')
            skt.settimeout(10)
            # TODO: check read return length
            try:
                r = skt.recv(num_to_read)
                print(r.hex())
                # r = skt.recv(1)
                print('finish reading')
            except socket.timeout:
                print('timeout')
                state = ERROR
                continue

            state = HANDSHAKE
            data += r
        elif state == HANDSHAKE:
            # header 6 byte
            # random 32
            # session id length(1) n
            # cipher suites length(2) n
            # compression method length(1) n
            # extension length(2)
            index = 5+6+32
            s_id_len = int.from_bytes(data[index:index+1], byteorder='big')
            print(f'session id length: {s_id_len}')
            index += 1+s_id_len

            c_s_len = int.from_bytes(data[index:index+2], byteorder='big')
            print(f'cipher suites length: {c_s_len}')
            index += 2+c_s_len

            c_m_len = int.from_bytes(data[index:index+1], byteorder='big')
            print(f'compression method length: {c_m_len}')
            index += 1+c_m_len

            ext_len = int.from_bytes(data[index:index+2], byteorder='big')
            print(f'extension length: {ext_len}')

            index += 2
            state = EXTENSION
        elif state == EXTENSION:
            # type(2)
            # length(2)
            print(data[index:index+2].hex())
            if data[index:index+2] == b'\x00\x00':
                state = SERVER_NAME
            else:
                index += 2
                length = int.from_bytes(data[index:index+2], byteorder='big')
                index += 2+length
            # break
        elif state == SERVER_NAME:
            # list length (2)
            # name type(1)
            # name length(2)
            index += 2
            length = int.from_bytes(data[index:index+2], byteorder='big')
            print(f'server name length: {length}')
            index += 2

            list_length = int.from_bytes(data[index:index+2], byteorder='big')
            print(f'name list length: {list_length}')
            index += 2

            name_type = int.from_bytes(data[index:index+1], byteorder='big')
            print(f'name type: {name_type}')
            index += 1

            name_length = int.from_bytes(data[index:index+2], byteorder='big')
            print(f'name length: {name_length}')
            index += 2

            hostname = data[index:index+name_length].decode()
            print(f'hostname: {hostname}')
            print(data.hex())
            # index += 2
            return hostname, data

        elif state == ERROR:
            print('Error state, close socket')
            skt.close()
            break

        if index >= len(data):
            print('end of data!', len(data))
            state = ERROR
