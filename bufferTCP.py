from packTCP import package

class buffer:
    def __init__(self, MAX_SIZE):
        self.data_list = []
        self.MAX_SIZE = MAX_SIZE
        self.window = MAX_SIZE
        self.last_ack = 0
        self.expected_ack = 0
        self.last_seq = 1

    def update_window(self, size):
        self.window = self.window - size
