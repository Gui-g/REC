from os import curdir
from headerTCP import header
from bufferTCP import buffer
from packTCP import package
import time




class manager:
    def __init__(self):
        self.manager_buffer = buffer(4096)
        self.connection_control = 0
        self.MTU = 100

    def byte_my_pack(self, pack):
        byted = str(pack.data) + pack.header.get_string()
        return bytes(byted, 'utf-8')

    def build_pack(self, header, data):
        return package(header, data)

    def decode_header(self, data):
        data = data.decode('utf-8')
        data = data.split('#')
        header = self.build_header(data[1], data[2], data[3], data[4], data[5], data[6])
        return header

    def decode_data(self, data):
        data = data.decode('utf-8')
        data = data.split('#')
        return data[0]

    def decode(self, data):
        decoded = package(self.decode_header(data), self.decode_data(data))
        return decoded

    def build_header(self, SYN, SEQ, ACK, FIN, LEN, window):
        new_header = header()
        new_header.make_header([int(SYN), int(SEQ), int(ACK), int(FIN), int(LEN), int(window)])
        return new_header

    def build_client_buffer(self, data):
        new_header = self.build_header(0,0,0,0,0,0)
        try_pack = self.byte_my_pack(self.build_pack(new_header, data))
        size = len(try_pack)*8 #1 byte = 8 bits

        self.manager_buffer.data_list.append(self.connection_start(1))

        if size >= self.MTU:
            max_size = int(self.MTU/8)
            split = [data[i:i + max_size] for i in range(0, len(data), max_size)]
            split = [self.byte_my_pack(self.build_pack(new_header, x)) for x in split]
            split[-1] = self.connection_end(split[-1])
            self.manager_buffer.data_list = self.manager_buffer.data_list + split
            return self.manager_buffer
        else:
            self.manager_buffer.data_list.append(try_pack)
            return self.manager_buffer 

    def connection_start(self, SEQ):
        fst_header = self.build_header(0,0,0,0,0,0)
        fst_header.make_SYN()
        fst_header.SEQ = SEQ
        fst_header.LEN = 0
        fst_pack = self.build_pack(fst_header, '')
        return self.byte_my_pack(fst_pack)

    def connection_end(self, data):
        last = self.decode(data)
        last.header.make_FIN()
        return self.byte_my_pack(last)

    def make_connection(self, data):
        data = self.decode(data)

        if data.header.SYN:
            data.header.ACK = 1
            return self.byte_my_pack(self.build_pack(data.header, data.data))
        else:
            return self.byte_my_pack(self.build_pack(data.header, data.data))

    def buffer_next_ack(self, size):
        self.manager_buffer.expected_ack = self.manager_buffer.last_seq + size

    #flag => 1 = client => update seq with next ack
    #2 = server => update ack with next ack
    def update_pack(self, pack, flag):
        if flag == 1:
            pack.header.SEQ = self.manager_buffer.expected_ack
            pack.header.ACK = self.manager_buffer.last_ack
            pack.header.LEN = len(pack.data)
        if flag == 2:
            pack.header.ACK = self.manager_buffer.expected_ack
            pack.header.LEN = len(pack.data)

    def update_buffer(self, SEQ, LEN, ACK):
        self.manager_buffer.last_seq = SEQ
        self.manager_buffer.last_ack = ACK
        self.buffer_next_ack(LEN)

    def switch_connection(self, state):
        if state:
            self.connection_control = 0
        else:
            self.connection_control = 1

    def server_pack(self, pack):
        current_pack = self.decode(pack)
        
        self.update_buffer(current_pack.header.SEQ, current_pack.header.LEN, current_pack.header.ACK)

        #SYN package
        if current_pack.header.FIN == 0 and self.connection_control == 0 and current_pack.header.SYN: 
            self.switch_connection(0)
            return self.make_connection(pack)
        #Not SYN not FIN
        elif current_pack.header.FIN == 0 and self.connection_control:
            self.update_pack(current_pack, 2)
            return self.byte_my_pack(current_pack)
        #FIN package
        else:
            self.update_pack(current_pack, 2)
            self.switch_connection(1)
            return self.byte_my_pack(current_pack)

    def client_pack(self, pack):
        current_pack = self.decode(pack)

        #SYN package => LEN doesn't matter, already has SEQ
        if current_pack.header.SYN and self.connection_control == 0:
            self.update_buffer(current_pack.header.SEQ, 0, current_pack.header.ACK)
            self.switch_connection(0)
            return pack
        elif current_pack.header.FIN == 0 and self.connection_control:
            self.update_pack(current_pack, 1)
            self.update_buffer(current_pack.header.SEQ, current_pack.header.LEN, current_pack.header.ACK)
            return self.byte_my_pack(current_pack)
        elif current_pack.header.FIN:
            self.switch_connection(1)
            self.update_pack(current_pack, 1)
            self.update_buffer(current_pack.header.SEQ, current_pack.header.LEN, current_pack.header.ACK)
            return self.byte_my_pack(current_pack)

    def client_resp_pack(self, response):
        current_pack = self.decode(response)

        print(current_pack.header.ACK)
        print(self.manager_buffer.expected_ack)
        if current_pack.header.ACK != self.manager_buffer.expected_ack:
            return 0
        else:
            return 1
            
def timeout():
    print('Starting function timeout()...')
    while True:
        time.sleep(1)
        print(next(counter))    

    return

#metodo 1 pré-response
#lê dado, sem seq, len, ack
#atualiza len = len(dado), seq = expected_ack, ack = last_ack
#envia dado
#metodo 2 pós-response
#recebe resposta
#verifica se ack resposta = next expected_ack