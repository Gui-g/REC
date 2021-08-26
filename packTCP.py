from headerTCP import header

class package:
    def __init__(self, header : header, data):
        self.header = header
        self.data = data

    def get_string(self):
        return str(self.data) + self.header.get_string()