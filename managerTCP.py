from os import curdir
from headerTCP import header
from bufferTCP import buffer
from packTCP import package
import multiprocessing.pool
import functools
import socket
import operator

class manager:
    def __init__(self):
        self.connection_control = 0
        self.MTU = 100
        self.server_adress : tuple
        self.socket : socket
        self.full_data = ''
        self.manager_buffer = buffer(1024, self.MTU)

    def create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close_socket(self):
        self.socket.close()

    def create_connection(self, IP, PORT):
        self.server_adress = (IP, PORT)
        self.socket.bind(self.server_adress)

    def client_send_package(self, data):
        #build buffer
        self.manager_buffer = self.build_client_buffer(data)
        
        #send SYN
        self.manager_buffer.data_list[0] = self.client_pack(self.manager_buffer.data_list[0])
        self.send_data(self.manager_buffer.data_list[0], self.server_adress)
        self.manager_buffer.snd_una = self.manager_buffer.snd_una + 1

        #receive SYN response
        response_syn, address = self.receive_data()
        rsp_syn_pck = self.decode_pack(response_syn)

        #CHECK SYNACK
        if rsp_syn_pck.header.SYN and rsp_syn_pck.header.ACK:
            self.manager_buffer.snd_nxt = self.manager_buffer.snd_nxt + 1
            
            final_package = 0
            start = self.manager_buffer.snd_nxt
            goal = self.manager_buffer.usable_wnd

            #while not over
            while not final_package:

                #10 -> usable_wmd = 19 => 19 (10+19 = 29) -> 19 => 19 (29+19 = 48), mas acaba no 38
                #if (start + self.manager_buffer.usable_wnd) > len(self.manager_buffer.data_list)
                #then limite = len() [0:20] => [20:40]
                #send window
                for i in range(start, start+goal-1):
                    print(i)
                    self.manager_buffer.data_list[i] = self.client_pack(self.manager_buffer.data_list[i])
                    self.send_data(self.manager_buffer.data_list[i], self.server_adress)
                    self.manager_buffer.snd_nxt = self.manager_buffer.snd_nxt + 1

                    if self.decode_header(self.manager_buffer.data_list[i]).FIN:
                        break
                
                #receive window
                rsp_list = []
                print(goal)
                for i in range(0, goal-1):
                    #receive response
                    print(i)
                    response, address = self.receive_data()
                    rsp_list.append(response)

                    if self.decode_header(response).FIN:
                        break

                #sort all responses by ack for window-checking
                rsp_list = self.sort_b_list(rsp_list)

                for response in rsp_list:
                    response = self.decode_pack(response)

                    #is response the expected ack?
                    #yes => send unackowledged + 1, send next + 1
                    #no => waste responses (think later what to do)
                    if self.client_resp_pack(response.header.ACK):
                        self.manager_buffer.snd_una = self.manager_buffer.snd_una + 1

                        if response.header.FIN:
                            final_package = 1
                    else:
                        continue

                self.manager_buffer.usable_wnd = self.manager_buffer.snd_una + self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt
                start = self.manager_buffer.snd_nxt
                goal = self.manager_buffer.usable_wnd

                if goal + start > len(self.manager_buffer.data_list):
                    goal = len(self.manager_buffer.data_list)

        #NOT SYNACK? TO DO
            

    def server_get_package(self):
        final_package = 0

        #wait for SYN
        syn_request, address = self.receive_data()
        self.manager_buffer.snd_una = 0

        #build answer => if SYN then SYNACK
        answer = self.server_pack(syn_request)
        ans_head = self.decode_header(answer)

        #if SYNACK then
        if ans_head.SYN and ans_head.ACK:
            #answer SYNACK and begin
            self.send_data(answer, address)
            self.manager_buffer.snd_nxt = 1
            start = self.manager_buffer.snd_una
            
            #while package has not been fully assembled
            while not final_package:

                for i in range(0, self.manager_buffer.usable_wnd-1):
                    data, address = self.receive_data()
                    data = self.server_pack(data)
                    
                    #if pack is repeated ignore
                    if not self.manager_buffer.data_list.count(data):
                        self.manager_buffer.data_list.append(data)
                        self.manager_buffer.snd_nxt = self.manager_buffer.snd_nxt + 1
                    
                        data_head = self.decode_header(data)

                        if data_head.FIN:
                            final_package = 1
                            break
                    else:
                        continue

                self.manager_buffer.data_list = self.sort_b_list(self.manager_buffer.data_list)
                #response window
                #just send everything
                for i in range(start, self.manager_buffer.snd_nxt-1):
                    self.send_data(self.manager_buffer.data_list[i], address)
                    self.manager_buffer.snd_una = self.manager_buffer.snd_una + 1

                    if self.decode_header(self.manager_buffer.data_list[i]).FIN:
                        print('breaked')
                        break

                self.manager_buffer.usable_wnd = 1 + self.manager_buffer.snd_una + self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt

                #if window is full or near clear space by assembling
                if self.manager_buffer.usable_wnd == 0 or self.manager_buffer.remaining_slots(self.MTU) < self.manager_buffer.usable_wnd:
                    print('assembled?!\n')
                    self.assemble_data()
                    self.manager_buffer.snd_nxt = 1
                    self.manager_buffer.snd_una = 0

                start = self.manager_buffer.snd_una

            self.assemble_data()

        self.manager_buffer.data_list.clear()
        
        print(self.full_data)
        self.full_data = ""
        #slow starter etc define qual o usable_wind inicial
        self.manager_buffer.usable_wnd = 5


    def send_data(self, data : bytes, address : tuple):
        data_header = self.decode_header(data)
        
        self.update_buffer(data_header, 1)
        
        sent = self.socket.sendto(data, address)
        print('sent {} bytes to {}'.format(sent, address))
        print('sent {}'.format(data))

    def receive_data(self):
        data, address = self.socket.recvfrom(4096)
        print('received {} bytes from {}'.format(len(data), address))
        print('received {!r}'.format(data)) 

        data_header = self.decode_header(data)

        self.update_buffer(data_header, 0)

        return (data, address)
#
#    def timeout(max_timeout):
#        """Timeout decorator, parameter in seconds."""
#        def timeout_decorator(item):
#            """Wrap the original function."""
#            @functools.wraps(item)
#            def func_wrapper(*args, **kwargs):
#                """Closure for function."""
#                pool = multiprocessing.pool.ThreadPool(processes=1)
#                async_result = pool.apply_async(item, args, kwargs)
#                # raises a TimeoutError if execution exceeds max_timeout
#                return async_result.get(max_timeout)
#            return func_wrapper
#        return timeout_decorator
#
    def byte_my_pack(self, pack : package) -> bytes:
        byted = str(pack.data) + pack.header.get_string()
        return bytes(byted, 'utf-8')

    def build_pack(self, header : header, data) -> package:
        return package(header, data)

    def decode_header(self, data : bytes) -> header:
        data = data.decode('utf-8')
        data = data.split('#')
        header = self.build_header(data[1], data[2], data[3], data[4], data[5], data[6])
        return header

    def decode_data(self, data : bytes):
        data = data.decode('utf-8')
        data = data.split('#')
        return data[0]

    def decode_pack(self, data : bytes) -> package:
        decoded = package(self.decode_header(data), self.decode_data(data))
        return decoded

    def build_header(self, SYN, SEQ, ACK, FIN, LEN, RWND):
        new_header = header()
        new_header.make_header([int(SYN), int(SEQ), int(ACK), int(FIN), int(LEN), int(RWND)])
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

    def assemble_data(self):
        for data_block in self.manager_buffer.data_list:
            data_block = self.decode_data(data_block)
            self.full_data = self.full_data + data_block
        self.manager_buffer.data_list.clear()

    def connection_start(self, SEQ):
        fst_header = self.build_header(0,0,0,0,0,0)
        fst_header.make_SYN()
        fst_header.SEQ = SEQ
        fst_header.LEN = 0
        fst_pack = self.build_pack(fst_header, '')
        return self.byte_my_pack(fst_pack)

    def connection_end(self, data):
        last = self.decode_pack(data)
        last.header.make_FIN()
        return self.byte_my_pack(last)

    def make_connection(self, data):
        data = self.decode_pack(data)
        #data.data = ""

        if data.header.SYN:
            data.header.ACK = self.manager_buffer.next_ack
            data.header.RWND = self.manager_buffer.MAX_SIZE
            return self.byte_my_pack(self.build_pack(data.header, data.data))
        else:
            return self.byte_my_pack(self.build_pack(data.header, data.data))

    #flag => 1 = client => update seq with next seq
    #2 = server => update ack with next ack
    def update_pack(self, pack):
            pack.header.SEQ = self.manager_buffer.next_seq
            pack.header.ACK = self.manager_buffer.next_ack
            pack.header.LEN = len(pack.data)
            pack.header.RWND = self.manager_buffer.window

    #flag => 1 = sending (rdy next seq) ; 0 = receiving (rdy next ack)
    def update_buffer(self, header : header, flag):
        if flag:
            self.manager_buffer.next_seq = header.SEQ + header.LEN
        else:
            self.manager_buffer.next_ack = header.SEQ + header.LEN
            self.manager_buffer.update_window(header.LEN)

            if header.SYN and header.ACK != 0:
                self.manager_buffer.window = header.RWND

    def sort_b_list(self, b_list):
        in_list = [self.decode_pack(x) for x in b_list]

        in_list.sort(key = lambda x: x.header.ACK)

        b_list = [self.byte_my_pack(x) for x in in_list]

        return b_list

    def switch_connection(self, state):
        if state:
            self.connection_control = 0
        else:
            self.connection_control = 1

    def server_pack(self, pack):
        current_pack = self.decode_pack(pack)
        #0 len response
        #current_pack.data = ""

        #SYN package
        if not current_pack.header.FIN and not self.connection_control and current_pack.header.SYN: 
            self.switch_connection(0)
            return self.make_connection(pack)
        #Not SYN not FIN
        elif not current_pack.header.FIN and self.connection_control:
            self.update_pack(current_pack)
            return self.byte_my_pack(current_pack)
        #FIN package
        else:
            self.update_pack(current_pack)
            self.switch_connection(1)
            return self.byte_my_pack(current_pack)

    #@timeout(5.0)
    def client_pack(self, pack):
        current_pack = self.decode_pack(pack)

        #SYN package => LEN doesn't matter, already has SEQ
        if current_pack.header.SYN and not self.connection_control:
            self.switch_connection(0)
            return pack
        elif not current_pack.header.FIN and self.connection_control:
            self.update_pack(current_pack)
            return self.byte_my_pack(current_pack)
        elif current_pack.header.FIN:
            self.switch_connection(1)
            self.update_pack(current_pack)
            return self.byte_my_pack(current_pack)

    def client_resp_pack(self, ACK):
        expected_rsp = self.decode_header(self.manager_buffer.data_list[self.manager_buffer.snd_una])

        if ACK != (expected_rsp.SEQ + expected_rsp.LEN):
            return 0
        else:
            return 1



    

#metodo 1 pré-response
#lê dado, sem seq, len, ack
#atualiza len = len(dado), seq = expected_ack, ack = last_ack
#envia dado
#metodo 2 pós-response
#recebe resposta
#verifica se ack resposta = next expected_ack