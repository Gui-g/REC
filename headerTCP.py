class header:
    def __init__(self):
        self.SYN = 0
        self.SEQ = 0
        self.ACK = 0
        self.FIN = 0
        self.LEN = 0
        self.RWND = 0

    def make_SYN(self):
        self.SYN = 1

    def make_not_SYN(self):
        self.SYN = 0

    def make_FIN(self):
        self.FIN = 1

    def make_not_FIN(self):
        self.FIN = 0

    def make_header(self, header):
        self.SYN = header[0]
        self.SEQ = header[1]
        self.ACK = header[2]
        self.FIN = header[3]
        self.LEN = header[4]
        self.RWND = header[5]

    def get_string(self):
        return str('#' + str(self.SYN) + '#' + str(self.SEQ) + '#' + str(self.ACK) + '#' + str(self.FIN) + '#' + str(self.LEN) + '#' + str(self.RWND))
