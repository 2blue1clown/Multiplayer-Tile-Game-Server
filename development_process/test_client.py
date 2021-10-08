import socket
import sys
import struct

messages = [ 'This is the message. ',
             'It will be sent ',
             'in parts.',
             ]
server_address = ('localhost', 10000)



# Create a TCP/IP socket
socks = [ socket.socket(socket.AF_INET, socket.SOCK_STREAM),
          socket.socket(socket.AF_INET, socket.SOCK_STREAM),
          ]

# Connect the socket to the port where the server is listening
print('connecting to {} port {}'.format(server_address[0],server_address[1]))
for s in socks:
    s.connect(server_address)


for message in messages:

    # Send messages on both sockets
    for s in socks:
        print('{}: sending {}'.format(s.getsockname(), message))
        s.send(bytes(message, 'utf-8'))

    # Read responses on both sockets
    for s in socks:
        data = s.recv(1024)
        print('{}: received {}'.format(s.getsockname(), data.decode('utf-8')))
        if not data:
            print('Closing socket'.format(s.getsockname()))
            s.close()
