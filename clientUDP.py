from managerTCP import manager

client_manager = manager()

# Create a UDP socket
client_manager.create_socket()

client_manager.server_adress = ('localhost', 10000)

lorem_ipsum = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

try:
    client_manager.client_send_package(lorem_ipsum)
finally:
    client_manager.close_socket()


