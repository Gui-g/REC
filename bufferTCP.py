from packTCP import package

class buffer:
    def __init__(self, MAX_SIZE, MTU):
        self.data_list = []
        self.MAX_SIZE = MAX_SIZE
        self.window = MAX_SIZE
        self.next_seq = 0
        self.next_ack = 0
        self.snd_una = 0
        self.snd_wnd = 0
        self.snd_nxt = 0
        self.cwnd = 1

    # cria um buffer de 1024 MTU de 100 => max 10 pacotes
    # snd_wnd = fixo 20 => depois do primeiro loop ele manda 0 + 20 - 0 => cwnd = 20

    def crnt_snd_wnd(self, MTU):
        limit = 0
        n_packs = 0

        for data in self.data_list[1:]:
            limit = limit + len(data)

            if limit > MTU:
                break

            n_packs = n_packs + 1
        
        self.snd_wnd = n_packs

    def crnt_rcv_wnd(self, data, MTU):
        self.snd_wnd = int(MTU / len(data))

    def max_packages(self, MTU):
        return int(self.MAX_SIZE / MTU)

    def update_window(self, size):
        self.window = self.window - size

    def remaining_slots(self, MTU):
        return int(self.window / MTU)
