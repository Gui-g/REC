from packTCP import package

class buffer:
    def __init__(self, MAX_SIZE, MTU):
        self.data_list = []
        self.MAX_SIZE = MAX_SIZE
        self.window = MAX_SIZE
        self.next_seq = 0
        self.next_ack = 0
        self.snd_una = 0
        self.snd_wnd = int(MAX_SIZE/MTU)
        self.snd_nxt = 0
        self.usable_wnd = 5

    #cria um buffer de 1024 MTU de 100 => max 10 pacotes
    #snd_wnd = fixo 20 => depois do primeiro loop ele manda 0 + 20 - 0 => usable_wnd = 20

    def current_window(self):
        current_size = 0

        for data in self.data_list:
            current_size = current_size + len(data)
        
        return

    def max_packages(self, MTU):
        return int(self.MAX_SIZE / MTU)

    def update_window(self, size):
        self.window = self.window - size

    def remaining_slots(self, MTU):
        return int(self.window / MTU)