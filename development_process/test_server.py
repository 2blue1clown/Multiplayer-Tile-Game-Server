
import socket
import sys
import tiles
import select
import queue
import random

MAX_ID = 3 # This is the highest possible id for a player (4 players is MAX_ID = 3)

live_idnums = []
names = {}
player_number = 0
placed_token = {} #Will be a list of bool to determine if the player has places a token yet
player_order = [] 

def welcome_client(connection, address, player_number):

    host, port = address
    name = '{}:{}'.format(host, port)

    idnum = player_number
    live_idnums.append(idnum)
    names[idnum] = name
    send_to(tiles.MessageWelcome(idnum).pack(),connection)

    if(player_number == MAX_ID):
        start_game()

def start_game():
    print("Starting game")
    for idnum in live_idnums:
        send_all(tiles.MessagePlayerJoined(names[idnum], idnum).pack())
        placed_token[idnum] = False

    send_all(tiles.MessageGameStart().pack())

    for sock in inputs:
        if sock is not server_sock:
            for _ in range(tiles.HAND_SIZE):
               tileid = tiles.get_random_tileid()
               send_to(tiles.MessageAddTileToHand(tileid).pack(),sock)

    while len(player_order) < (MAX_ID+1):
        rand_player = random.randint(0,MAX_ID)
        if rand_player not in player_order:
            player_order.append(rand_player)
    
    print(player_order)

    
    send_all(tiles.MessagePlayerTurn(next_turn()).pack()) 


#returns the numid of the next player
def next_turn(): #! WHAT HAPPENS WHEN A ALL PLAYERS ARE ELIMINATED? 
    next_player = player_order.pop(0)
    player_order.append(next_player)
    print("Sent next turn to {}".format(next_player))
    return next_player


    
def send_to(msg, sock):
    message_queues[sock].put(msg)
    # Add output channel for response
    if sock not in outputs:
        outputs.append(sock)

def send_all(msg):
    for sock in inputs:
        if sock is server_sock:
            continue
        else:
            message_queues[sock].put(msg)
            if sock not in outputs:
                outputs.append(sock)


# create a TCP/IP socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# listen on all network interfaces
server_address = ('', 30020)
server_sock.bind(server_address)

print('listening on {}'.format(server_sock.getsockname()))

server_sock.listen(5)

inputs = [ server_sock ]
outputs = [ ]

message_queues = {}

board = tiles.Board()

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
            welcome_client(connection,client_address,player_number)
            player_number += 1
            

        else:
            data = s.recv(4096)
            if data:
                # A readable client socket has data
                msg, consumed = tiles.read_message_from_bytearray(data)
                idnum = msg.idnum

                if not consumed:
                    break

                print('received message {}'.format(msg))

                # sent by the player to put a tile onto the board (in all turns except
                # their second)
                if isinstance(msg, tiles.MessagePlaceTile):
                    if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
                    # notify client that placement was successful
                        send_all(msg.pack())
                    # check for token movement
                    positionupdates, eliminated = board.do_player_movement(live_idnums)

                    for msg in positionupdates:
                        send_all(msg.pack())
                    
                    # need to check for any eliminations
                    for id in eliminated:
                            if id in player_order:
                                send_all(tiles.MessagePlayerEliminated(id).pack())
                                print("Player {} eliminated".format(id))
                                player_order.remove(id)
                        

                    # pickup a new tile
                    tileid = tiles.get_random_tileid()
                    send_to(tiles.MessageAddTileToHand(tileid).pack(),s)

                    # start next turn 
                    # next_turn uses a queue to keep track of whose turn it is.
                    if placed_token[idnum]:
                        send_all(tiles.MessagePlayerTurn(next_turn()).pack())
                        
                    else:
                        send_all(tiles.MessagePlayerTurn(idnum).pack())
                        print("{} gets another turn".format(idnum))


                # sent by the player in the second turn, to choose their token's
                # starting path
                elif isinstance(msg, tiles.MessageMoveToken):
                    if not board.have_player_position(msg.idnum):
                        if board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
                            # check for token movement

                            ## Keep a track of whether or not we have a placed token
                            placed_token[msg.idnum] = True
                            positionupdates, eliminated = board.do_player_movement(live_idnums)

                            for msg in positionupdates:
                                send_all(msg.pack())
                            
                            # need to check for any eliminations
                            for id in eliminated:
                                    if id in player_order:
                                        send_all(tiles.MessagePlayerEliminated(id).pack())
                                        print("Player {} eliminated".format(id))
                                        player_order.remove(id)
                            #if idnum in eliminated:
                             #   send_all(tiles.MessagePlayerEliminated(idnum).pack())
                              #  print("PLAYER ELIMINATED THIS NEEDS TO CHANGE SOMETHING" )
                               # player_order.remove(msg.idnum)
                            
                            # start next turn
                            send_all(tiles.MessagePlayerTurn(next_turn()).pack())

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

                


