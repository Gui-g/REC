from headerTCP import header
from bufferTCP import buffer
from packTCP import package
import socket


class manager:
    def __init__(self):
        self.connection_control = 0
        self.MTU = 500 
        self.server_adress: tuple
        self.socket: socket
        self.full_data = ''
        self.manager_buffer = buffer(4096, self.MTU)
        self.ssthresh = 2

    def create_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close_socket(self):
        self.socket.close()

    def create_connection(self, IP, PORT):
        self.server_adress = (IP, PORT)
        self.socket.bind(self.server_adress)

    def client_send_package(self, data):
        # build buffer
        self.manager_buffer = self.build_client_buffer(data)
        self.manager_buffer.crnt_snd_wnd(self.MTU)

        # send SYN
        self.manager_buffer.data_list[0] = self.client_pack(
            self.manager_buffer.data_list[0])
        self.send_data(self.manager_buffer.data_list[0], self.server_adress)
        self.manager_buffer.snd_una = self.manager_buffer.snd_una + 1

        # receive SYN response
        response_syn, address = self.receive_data()
        rsp_syn_pck = self.decode_to_pack(response_syn)

        # CHECK SYNACK
        if rsp_syn_pck.header.SYN and rsp_syn_pck.header.ACK:
            self.manager_buffer.snd_nxt = self.manager_buffer.snd_nxt + 1

            final_package = 0
            start = self.manager_buffer.snd_nxt
            goal = self.manager_buffer.cwnd

            # while not over
            while not final_package:
                for i in range(start, start+goal):
                    self.manager_buffer.data_list[i] = self.client_pack(
                        self.manager_buffer.data_list[i])
                    self.send_data(
                        self.manager_buffer.data_list[i], self.server_adress)
                    self.manager_buffer.snd_nxt = self.manager_buffer.snd_nxt + 1

                    if self.decode_to_header(self.manager_buffer.data_list[i]).FIN:
                        break
                print('----------------------------------------------------------------------------------')
                # receive window
                rsp_list = []
                for i in range(goal):
                    # receive response
                    response, address = self.receive_data()
                    rsp_list.append(response)

                    if self.decode_to_header(response).FIN:
                        break

                # sort all responses by ack for window-checking
                rsp_list = self.sort_b_list(rsp_list)

                for response in rsp_list:
                    response = self.decode_to_pack(response)

                    # is response the expected ack?
                    # yes => send unackowledged + 1, send next + 1
                    # no => waste responses (think later what to do)
                    if self.client_resp_pack(response.header.ACK):
                        # if self.manager_buffer.cwnd <= self.ssthresh:
                        self.manager_buffer.snd_una = self.manager_buffer.snd_una + 1  # slow start
                        # else:
                        # self.fastRecovery()

                        if response.header.FIN:
                            final_package = 1
                    else:
                        continue

                if(self.manager_buffer.cwnd < self.manager_buffer.snd_una +
                   self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt) and (2 ** self.ssthresh < self.manager_buffer.snd_una +
                                                                                   self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt):
                    self.manager_buffer.cwnd = (
                        2 ** self.ssthresh)  # slow start
                    self.ssthresh = self.ssthresh + 1
                else:
                    self.manager_buffer.cwnd = self.manager_buffer.snd_una + \
                        self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt  # window disp

                start = self.manager_buffer.snd_nxt
                goal = self.manager_buffer.cwnd

                if goal + start > len(self.manager_buffer.data_list):
                    goal = len(self.manager_buffer.data_list)

        self.ssthresh = 2

        # NOT SYNACK? TO DO

    def server_get_package(self):
        final_package = 0

        # wait for SYN
        syn_request, address = self.receive_data()
        self.manager_buffer.snd_una = 0

        # build answer => if SYN then SYNACK
        answer = self.server_pack(syn_request)
        ans_head = self.decode_to_header(answer)

        # if SYNACK then
        if ans_head.SYN and ans_head.ACK:
            # answer SYNACK and begin
            self.send_data(answer, address)
            self.manager_buffer.snd_nxt = 1
            start = self.manager_buffer.snd_una

            print(self.manager_buffer.cwnd)

            # while package has not been fully assembled
            while not final_package:
                for i in range(self.manager_buffer.cwnd):
                    data, address = self.receive_data()
                    self.manager_buffer.crnt_rcv_wnd(data, self.MTU)
                    data = self.server_pack(data)

                    # if pack is repeated ignore
                    if not self.manager_buffer.data_list.count(data):
                        self.manager_buffer.data_list.append(data)
                        self.manager_buffer.snd_nxt = self.manager_buffer.snd_nxt + 1

                        data_head = self.decode_to_header(data)

                        if data_head.FIN:
                            final_package = 1
                            break
                    else:
                        continue

                print('----------------------------------------------------------------------------------')
                self.manager_buffer.data_list = self.sort_b_list(
                    self.manager_buffer.data_list)
                # response window
                # just send everything
                for i in range(start, start + self.manager_buffer.cwnd):
                    self.send_data(self.manager_buffer.data_list[i], address)
                    self.manager_buffer.snd_una = self.manager_buffer.snd_una + 1

                    if self.decode_to_header(self.manager_buffer.data_list[i]).FIN:
                        break
                        # se cwnd < tamanho max disponivel && ssthresh < tamanho max disponivel
                if(self.manager_buffer.cwnd < self.manager_buffer.snd_una +
                   self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt) and (2 ** self.ssthresh < self.manager_buffer.snd_una +
                                                                                   self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt):
                    self.manager_buffer.cwnd = (
                        2 ** self.ssthresh)  # slow start
                    self.ssthresh = self.ssthresh + 1
                else:
                    self.manager_buffer.cwnd = 1 + self.manager_buffer.snd_una + \
                        self.manager_buffer.snd_wnd - self.manager_buffer.snd_nxt  # max disp

                # if window is full or near clear space by assembling
                if self.manager_buffer.cwnd == 0 or self.manager_buffer.remaining_slots(self.MTU) < self.manager_buffer.cwnd:
                    self.assemble_data()
                    self.manager_buffer.snd_nxt = 1
                    self.manager_buffer.snd_una = 0

                start = self.manager_buffer.snd_una

            self.assemble_data()

        self.manager_buffer.data_list.clear()

        print(self.full_data)
        self.full_data = ""

        # initial cwnd to slow start
        self.manager_buffer.cwnd = 1
        self.ssthresh = 2

        # if (timeout) == True:
        #    self.manager_buffer.ssthresh = self.manager_buffer.cwnd / 2,
        #    self.manager_buffer.cwnd = 1

    def send_data(self, data: bytes, address: tuple):
        data_header = self.decode_to_header(data)

        self.update_buffer(data_header, 1)

        sent = self.socket.sendto(data, address)
        print('sent {} bytes to {}'.format(sent, address))
        print('sent {}'.format(data))

    def receive_data(self):
        data, address = self.socket.recvfrom(4096)
        print('received {} bytes from {}'.format(len(data), address))
        print('received {!r}'.format(data))

        data_header = self.decode_to_header(data)

        self.update_buffer(data_header, 0)

        return (data, address)

    def byte_my_pack(self, pack: package) -> bytes:
        byted = str(pack.data) + pack.header.get_string()
        return bytes(byted, 'utf-8')

    def build_pack(self, header: header, data) -> package:
        return package(header, data)

    def decode_to_header(self, data: bytes) -> header:
        data = data.decode('utf-8')
        data = data.split('#')
        header = self.build_header(
            data[1], data[2], data[3], data[4], data[5], data[6])
        return header

    def decode_to_data(self, data: bytes):
        data = data.decode('utf-8')
        data = data.split('#')
        return data[0]

    def decode_to_pack(self, data: bytes) -> package:
        decoded = package(self.decode_to_header(data),
                          self.decode_to_data(data))
        return decoded

    def build_header(self, SYN, SEQ, ACK, FIN, LEN, RWND):
        new_header = header()
        new_header.make_header(
            [int(SYN), int(SEQ), int(ACK), int(FIN), int(LEN), int(RWND)])
        return new_header

    def build_client_buffer(self, data):
        new_header = self.build_header(0, 0, 0, 0, 0, 0)
        try_pack = self.byte_my_pack(self.build_pack(new_header, data))
        size = len(try_pack)*8  # 1 byte = 8 bits

        self.manager_buffer.data_list.append(self.connection_start(1))

        if size >= self.MTU:
            max_size = int(self.MTU/8)
            split = [data[i:i + max_size]
                     for i in range(0, len(data), max_size)]
            split = [self.byte_my_pack(
                self.build_pack(new_header, x)) for x in split]
            split[-1] = self.connection_end(split[-1])
            self.manager_buffer.data_list = self.manager_buffer.data_list + split
            return self.manager_buffer
        else:
            self.manager_buffer.data_list.append(try_pack)
            return self.manager_buffer

    def assemble_data(self):
        for data_block in self.manager_buffer.data_list:
            data_block = self.decode_to_data(data_block)
            self.full_data = self.full_data + data_block
        self.manager_buffer.data_list.clear()

    def connection_start(self, SEQ):
        fst_header = self.build_header(0, 0, 0, 0, 0, 0)
        fst_header.make_SYN()
        fst_header.SEQ = SEQ
        fst_header.LEN = 0
        fst_pack = self.build_pack(fst_header, '')
        return self.byte_my_pack(fst_pack)

    def connection_end(self, data):
        last = self.decode_to_pack(data)
        last.header.make_FIN()
        return self.byte_my_pack(last)

    def make_connection(self, data):
        data = self.decode_to_pack(data)

        if data.header.SYN:
            data.header.ACK = self.manager_buffer.next_ack
            data.header.RWND = self.manager_buffer.MAX_SIZE
            return self.byte_my_pack(self.build_pack(data.header, data.data))
        else:
            return self.byte_my_pack(self.build_pack(data.header, data.data))

    # flag => 1 = client => update seq with next seq
    # 2 = server => update ack with next ack
    def update_pack(self, pack):
        pack.header.SEQ = self.manager_buffer.next_seq
        pack.header.ACK = self.manager_buffer.next_ack
        pack.header.LEN = len(pack.data)
        pack.header.RWND = self.manager_buffer.window

    # flag => 1 = sending (rdy next seq) ; 0 = receiving (rdy next ack)
    def update_buffer(self, header: header, flag):
        if flag:
            self.manager_buffer.next_seq = header.SEQ + header.LEN
        else:
            self.manager_buffer.next_ack = header.SEQ + header.LEN
            self.manager_buffer.update_window(header.LEN)

            if header.SYN and header.ACK != 0:
                self.manager_buffer.window = header.RWND

    def sort_b_list(self, b_list):
        in_list = [self.decode_to_pack(x) for x in b_list]

        in_list.sort(key=lambda x: x.header.ACK)

        b_list = [self.byte_my_pack(x) for x in in_list]

        return b_list

    def switch_connection(self, state):
        if state:
            self.connection_control = 0
        else:
            self.connection_control = 1

    def server_pack(self, pack):
        current_pack = self.decode_to_pack(pack)

        # SYN package
        if not current_pack.header.FIN and not self.connection_control and current_pack.header.SYN:
            self.switch_connection(0)
            return self.make_connection(pack)
        # Not SYN not FIN
        elif not current_pack.header.FIN and self.connection_control:
            self.update_pack(current_pack)
            return self.byte_my_pack(current_pack)
        # FIN package
        else:
            self.update_pack(current_pack)
            self.switch_connection(1)
            return self.byte_my_pack(current_pack)

    def client_pack(self, pack):
        current_pack = self.decode_to_pack(pack)

        # SYN package => LEN doesn't matter, already has SEQ
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
        expected_rsp = self.decode_to_header(
            self.manager_buffer.data_list[self.manager_buffer.snd_una])

        if ACK != (expected_rsp.SEQ + expected_rsp.LEN):
            return 0
        else:
            return 1
