
import socket
import sys
import tiles
import select
import queue

# create a TCP/IP socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# listen on all network interfaces
server_address = ('localhost', 10000)
server_sock.bind(server_address)

print('listening on {}'.format(server_sock.getsockname()))

server_sock.listen(5)

inputs = [ server_sock ]
outputs = [ ]

message_queues = {}

while inputs:

    # wait for at least one of the sockets to be ready for processing
    print("Waiting for next event")
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    # handle inputs

    for s in readable:
        if s is server_sock:
            # This means that there is a new connection that is wanting to be made
            connection, client_address = s.accept()
            print("New connection from {}".format(client_address))
            connection.setblocking(0)
            inputs.append(connection)
            
            # Give the new connection a queue
            message_queues[connection] = queue.Queue()

            # Welcome the client to the game
            #welcome_client(connection,client_address)

        else:
            data = s.recv(1024)
            if data:
                # A readable client socket has data
                print("Received {} from {}".format(data, s.getpeername()))
                message_queues[s].put(data)
                # Add to output channel for response
                if s not in outputs:
                    outputs.append(s)

            else:
                # A readable client socket with no data has disconnected
                print("Closing {} after reading no data".format(s.getpeername()))
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close

                del message_queues[s]

    for s in writable:
        try:
            next_msg = message_queues[s].get_nowait()
        except queue.Empty:
            # No messages waiting so stop checking for writability
            print("Output queue for {} is empty".format(s.getpeername()))
            outputs.remove(s)

        else:
            print("Sending {} to {}".format(next_msg, s.getpeername()))
            s.send(next_msg)
    
    # Handle "exceptional conditions"
    for s in exceptional:
        print('Handling exceptional condition for{}'.format(s.getpeername()))
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del message_queues[s]

                


