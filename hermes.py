import game_master
import socket
import sys
import select
import queue
import random
import tiles


class Hermes(object): #This is the server and messenger
    
    def __init__(self, server_address, number_allowed_connections,number_of_players):
        self.server_address = server_address
        self.number_allowed_connections = number_allowed_connections
        self.number_of_players = number_of_players
        self.inputs = []
        self.outputs = []
        self.message_queues = {}
        # create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.game_master = game_master.GameMaster(self,self.number_of_players) #TODO check if this is the correct thing to do


    def read_socket(self,s):
        if s is self.sock:
            self.new_connection(s)
        
        else:
            data = s.recv(4096)

            if data:
                self.process_data(data)
            else:
                self.disconnect_client(s)
    
    def write_socket(self, s):
        try:
            next_msg = self.message_queues[s].get_nowait()
        except queue.Empty:
            # No messages waiting so stop checking for writability
            print("HERMES: Output queue for {} is empty".format(s.getpeername()))
            self.outputs.remove(s)

        else:
            #print("Sending {} to {}".format(next_msg, s.getpeername()))
            s.send(next_msg)
    
    def handle_socket(self, s):
        print('Handling exceptional condition for{}'.format(s.getpeername()))
        # Stop listening for input on the connection
        self.inputs.remove(s)

        if s in self.outputs:
            self.outputs.remove(s)
        s.close()

        # Remove message queue
        del self.message_queues[s]

    def new_connection(self, s):
        # This means that there is a new connection that is wanting to be made
        connection, client_address = s.accept()
        print("HERMES: New connection from {}".format(client_address))
        connection.setblocking(0)
        self.inputs.append(connection)
        
        # Give the new connection a queue
        self.message_queues[connection] = queue.Queue()

        # Welcome the client to the game
        self.game_master.new_client(connection,client_address)
        

    def process_data(self, data):

        # A readable client socket has data
        msg, consumed = tiles.read_message_from_bytearray(data)

        if not consumed:
            return #TODO: maybe this could throw an exception

        if isinstance(msg, tiles.MessagePlaceTile):
            self.game_master.place_tile(msg)
        
        if isinstance(msg,tiles.MessageMoveToken):
            self.game_master.move_token(msg)
    
    def send_all(self, msg):
        for sock in self.inputs:
            if sock is self.sock:
                continue
            else:
                self.message_queues[sock].put(msg)
                if sock not in self.outputs:
                    self.outputs.append(sock)
    
    def send_to(self, msg, connection): #Connection is the socket for that connection
        self.message_queues[connection].put(msg)
        # Add output channel for response
        if connection not in self.outputs:
            self.outputs.append(connection)

    def start_server(self):
        # listen on all network interfaces
        self.sock.bind(self.server_address)
        self.sock.listen(self.number_allowed_connections)
        self.inputs.append(self.sock)


        while self.inputs:
            # wait for at least one of the sockets to be ready for processing
            print("HERMES: Waiting for next event")
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs)

            for socket in readable:
                self.read_socket(socket)

            for socket in writable:
                self.write_socket(socket)
            
            for socket in exceptional:
                self.handle_socket(socket)

    def shut_down(self):
        self.sock.close()
        print('HEREMES: Shutting down')

    def disconnect_client(self, s):
        # A readable client socket with no data has disconnected
        print("HERMES: Closing {} after reading no data".format(s.getpeername()))
        if s in self.outputs:
            self.outputs.remove(s)
        self.inputs.remove(s)
        s.close()

        del self.message_queues[s]

        self.game_master.remove_client(s)