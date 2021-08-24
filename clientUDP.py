import socket
from managerTCP import manager
from itertools import count
import multiprocessing
import multiprocessing_import_timeout

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 10000)

client_manager = manager()
lorem_ipsum = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
buffer = client_manager.build_client_buffer(lorem_ipsum)
counter = count(0)

try:
    for data in buffer.data_list:

        #Send data
        print('\nsending {!r}'.format(data))
        data = client_manager.client_pack(data)

        sent = sock.sendto(data, server_address)
        p1 = multiprocessing.Process(target=multiprocessing_import_timeout.timeout)

        
        #Receive response
        print('\nwaiting to receive')
        response, server = sock.recvfrom(4096)
        print('received {!r}'.format(response))  

        if client_manager.client_resp_pack(response):
            continue
        else:
            break
        
#deadline = time.time() + 20.0
#while not data_received:
#    if time.time() >= deadline:
#        raise Exception() # ...
#    socket.settimeout(deadline - time.time())
#    socket.read() # ...
   
finally:
    print('closing socket')
    sock.close()