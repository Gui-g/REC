from packTCP import package

class buffer:
    def __init__(self, MAX_SIZE):
        self.data_list = []
        self.MAX_SIZE = MAX_SIZE
        self.next_seq = 0
        self.next_ack = 0
        self.snd_una = 0
        self.snd_wnd = 20
        self.snd_nxt = 0
        self.usable_wnd = 20

    def current_window(self):
        current_size = 0

        for data in self.data_list:
            current_size = current_size + len(data)
        
        return self.MAX_SIZE - current_size