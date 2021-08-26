from managerTCP import manager

server_manager = manager()

# Create a UDP socket
server_manager.create_socket()

# Bind the socket to the port
server_manager.create_connection('localhost', 10000)

while True:
    server_manager.server_get_package()
