# Author name: Jonathan Jones
# Student number: 22479345
# Date 14 May 2021

import socket
import tiles
import select
import queue
import random
import time


# This is a class that is used to keep track of player info
class Player():
    def __init__(self, connection):
        self.connection = connection
        self.placed_token = False
        self.idnum = game_master.free_id()
        self.hand = []
        self.first_turn = True

# This is a class to log any messages sent to all with send_all()
# It also brings clients that join late up to speed.
class Logger():
    def __init__(self):
        self.log = [] # this is the log of messages with index 0 being the earliest message

    # add a message to the log   
    def add(self, msg):
        self.log.append(msg)

    # used on new spectator clients to bring them up to the current game turn 
    def update_client(self,client_connection):
        print("Updating {}".format(client_connection.getpeername()))
        for msg in self.log:
            send_to(msg,client_connection)

# Handles the game logic
class GameMaster():
    def __init__(self):
        self.turn_start_time = 0
        self.in_game = False

    def start_game(self):
        # Make all of the games records again
        self.board = tiles.Board()
        self.in_game = True
        self.first_turn = True
        self.players={}
        self.player_order = []
        self.current_turn = -1

        self.pick_players() # Picks who is a user and who is a player
        # set player order.
        for player in self.players.values():
            self.player_order.append(player.idnum)

        self.welcome() # Welcomes all players 
        self.players_joined() # Lets players know of other players

        send_all(tiles.MessageGameStart().pack()) # Let all connections know game starts 
        self.cycle_player_turns() # Lets the clients know the turn order

        # send all players their tiles
        for player in self.players.values():
            for _ in range(tiles.HAND_SIZE):
                tileid = tiles.get_random_tileid()
                send_to(tiles.MessageAddTileToHand(tileid).pack(),player.connection)
                player.hand.append(tileid)

        self.next_turn()
        return

    #next_turn will check if the game is finished as well
    def next_turn(self): 
        #check if this is the first tern of the game
        if self.is_finished():
            self.finish_game()
            return
        if self.current_turn != -1:
            player = self.players[self.current_turn]
        if self.first_turn:
            next_player = self.player_order.pop(0)
            self.player_order.append(next_player)
            print("GM: Player {} goes first".format(next_player))
            self.first_turn = False
            print(self.player_order)
        #check if the previous turn's player has placed their token
        elif not player.first_turn:
            next_player = self.player_order.pop(0)
            self.player_order.append(next_player)
            print("GM: Sent next turn to {}".format(next_player))
        else:
            next_player = player.idnum
            player.first_turn = False
            print("GM: Player {} gets another turn".format(next_player))
        send_all(tiles.MessagePlayerTurn(next_player).pack())
        self.current_turn = next_player
        self.turn_start_time = time.perf_counter()
        return


    def do_eliminations(self,eliminated):
        # need to check for any eliminations
        for idn in eliminated:
            if idn in self.player_order:
                send_all(tiles.MessagePlayerEliminated(idn).pack())
                self.remove_from_player_order(idn)


    def place_tile(self,msg):
        if self.current_turn != msg.idnum:
            print('GM: {} tried to place a tile when its not their turn. whose_turn = {}'.format(msg.idnum,self.current_turn))
    
            return
        elif self.board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
            msg_player = self.players[msg.idnum]
            try:
                msg_player.hand.remove(msg.tileid)
            except ValueError:
                raise Exception("cannot remove tile since its not in the players hand")

            # notify client that placement was successful
            send_all(msg.pack())
            # check for token movement
            positionupdates, eliminated = self.board.do_player_movement(self.player_order)

            for msg in positionupdates:
                send_all(msg.pack())
            
            # pickup a new tile
            tileid = tiles.get_random_tileid()
            send_to(tiles.MessageAddTileToHand(tileid).pack(),msg_player.connection)
            msg_player.hand.append(tileid)
            # check and send messages for eliminations
            self.do_eliminations(eliminated)
                
            # start next turn 
            self.next_turn()

    def move_token(self,msg):
        if self.current_turn != msg.idnum:
            return
        elif not self.board.have_player_position(msg.idnum):
            if self.board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
                #DEBUG print("GM: token moved by {}".format(msg.idnum))
                msg_player = self.players[msg.idnum]

                # Keep a track of whether or not we have a placed token
                msg_player.placed_token = True

                # check for token movement
                positionupdates, eliminated = self.board.do_player_movement(self.player_order)

                for msg in positionupdates:
                    send_all(msg.pack())
                
                # need to check for any eliminations
                self.do_eliminations(eliminated)
                
                # start next turn
                self.next_turn()
    

    def is_finished(self) -> bool:
        #DEBUG print('GM: len(players): {}'.format(len(self.players)))
        if len(self.player_order)<2:
            return True
        else:
            return False
    
    def finish_game(self):
        self.in_game = False
        print("GAME FINISHED!")
        send_all(tiles.MessageCountdown().pack())

    def pick_players(self):
        users = inputs.copy()
        users.remove(serversock)
        while len(self.players) < PLAYER_LIMIT and len(users) > 0:
            index = random.randint(0,len(users)-1)
            connection = users.pop(index)
            player = Player(connection)
            self.players[player.idnum] = player
        return
            
    def welcome(self):
        for player in self.players.values():
            print('GM: welcoming: {} as {}'.format(player.connection,player.idnum))
            send_to(tiles.MessageWelcome(player.idnum).pack(),player.connection)
        return

    def players_joined(self):
        for player in self.players.values():
            send_all(tiles.MessagePlayerJoined("".format(player.idnum),player.idnum).pack())
        return
            
    
    def free_id(self) -> int:
        if(len(self.players)>=PLAYER_LIMIT):
            raise Exception("GM: Too many players")
        for idnum in range(PLAYER_LIMIT):
            if idnum not in self.players.keys():
                break
        return idnum

    def cycle_player_turns(self):
        print('GM: Cycling Players.. player_order length : {}'.format(len(self.player_order)))
        for player in self.player_order:
            send_all(tiles.MessagePlayerTurn(player).pack())

    def change_player_to_user(self, idnum):
        try:
            player = self.players.pop(idnum)
            player = player.become_user()
        except KeyError:
            return
        #DEBUG print("GM: Player {} changed to user".format(idnum))
    
    def remove_from_player_order(self, idnum):
        self.player_order.remove(idnum)
        return
    
    def disconnect_player(self,connection):
        for player in self.players.values():
            if connection is player.connection:
                if player.idnum in self.player_order and self.in_game:
                    send_all(tiles.MessagePlayerEliminated(player.idnum).pack())
                    self.remove_from_player_order(player.idnum)
                send_all(tiles.MessagePlayerLeft(player.idnum).pack())
                if player.idnum == self.current_turn:
                    self.first_turn = True
                    self.next_turn()
    
    def random_turn(self):
        print("GM is taking this turn for you")
        player = self.players[self.current_turn]
        #TODO I used first turn for something else so i should change that 
        if player.first_turn:
            self.random_place_tile()
        elif not player.placed_token:
            self.pick_random_token_position()
        elif player.placed_token:
            self.random_place_tile()
    
    # I will need to be keeping a record of every tile that the players have in
    # their player object
    def random_place_tile(self):
        player = self.players[self.current_turn]
        print("GM: Taking turn for {}".format(player.idnum))
        random_index = random.randint(0,len(player.hand)-1)
        random_tile_id = player.hand.pop(random_index)
        rotation = random.randint(0,3)
        while True:
            x = random.randint(0,4)
            y = random.randint(0,4)
            print("GM: Trying x {} and y {}".format(x,y))            
            if self.board.set_tile(x, y, random_tile_id, rotation, player.idnum):
                break
        
        msg = tiles.MessagePlaceTile(player.idnum,random_tile_id,rotation,x,y)

        # notify client that placement was successful
        send_all(msg.pack())
        # check for token movement
        positionupdates, eliminated = self.board.do_player_movement(self.player_order)

        for msg in positionupdates:
            send_all(msg.pack())
        
        # pickup a new tile
        tileid = tiles.get_random_tileid()
        send_to(tiles.MessageAddTileToHand(tileid).pack(),player.connection)
        player.hand.append(tileid)
        # check and send messages for eliminations
        self.do_eliminations(eliminated)
            
        # start next turn 
        self.next_turn()
    
    def pick_random_token_position(self):
        player = self.players[self.current_turn]
        print("GM: Placing token for {}".format(player.idnum))
        while True:
            x = random.randint(0,4)
            y = random.randint(0,4)
            position = random.randint(0,7)
            print("GM: Trying x {} and y {} and position {}".format(x,y,position))            
            if self.board.set_player_start_position(player.idnum,x,y,position):
                break
        #DEBUG print("GM: token moved by {}".format(msg.idnum))

        # Keep a track of whether or not we have a placed token
        player.placed_token = True

        # check for token movement
        positionupdates, eliminated = self.board.do_player_movement(self.player_order)

        for msg in positionupdates:
            send_all(msg.pack())
        
        # need to check for any eliminations
        self.do_eliminations(eliminated)
        
        # start next turn
        self.next_turn()
        



                



## Server Variables and Constants 


ALLOWED_CONNECTIONS = 100
PLAYER_LIMIT = tiles.PLAYER_LIMIT 
COOLDOWN_TIME = 2 # seconds
MAX_TURN_TIME = 10 #seconds

SELECT_TIMEOUT = 1

inputs = [] # This will serve as a total record for all the connections
outputs = [] # This will be used to keep track of which connections need to be sent something
message_queues = {}


## Server functions
def send_all(msg):

    global message_queues
    global outputs


    logger.add(msg) 
    print("HERMES: Sending to all {}".format(tiles.read_message_from_bytearray(msg)))
    
    for sock in inputs:
        if sock is serversock:
            continue
        else:
            #
            message_queues[sock].put(msg)
            if sock not in outputs:
                outputs.append(sock)
    return

def send_to(msg, connection): #Connection is the socket for that connection

    global message_queues
    global outputs

    message_queues[connection].put(msg)
    # Add output channel for response
    if connection not in outputs:
        print("HERMES: Sending to just{}, {}".format(connection.getpeername(),tiles.read_message_from_bytearray(msg)))
        outputs.append(connection)
    return
    

def write_socket(s):
    global message_queues
    global outputs
    try:
        next_msg = message_queues[s].get_nowait()
    except queue.Empty:
        # No messages waiting so stop checking for writability
        outputs.remove(s)
    except KeyError:
        print("This socket has abruptly disconnected")
        return


    else:
        #print("Sending {} to {}".format(next_msg, s.getpeername()))
        s.send(next_msg)

def handle_socket(self, s):
    global inputs
    global outputs
    global message_queues
    print('Handling exceptional condition for{}'.format(s.getpeername()))
    # Stop listening for input on the connection
    inputs.remove(s)

    if s in outputs:
        outputs.remove(s)
    s.close()

    # Remove message queue
    del message_queues[s]
    return

def new_connection(s):
    global inputs
    global outputs
    global message_queues
    # This means that there is a new connection that is wanting to be made
    connection, client_address = s.accept()
    # DEBUG print("HERMES: New connection from {}".format(client_address))
    connection.setblocking(0)
    inputs.append(connection)
    
    # Give the new connection a queue
    message_queues[connection] = queue.Queue()

    # Welcome the client to the game
    if game_master.in_game:
        logger.update_client(connection)
    

    return
    

def process_data(data):

    # A readable client socket has data
    msg, consumed = tiles.read_message_from_bytearray(data)

    if not consumed:
        return #TODO: maybe this could throw an exception

    if isinstance(msg, tiles.MessagePlaceTile):
        game_master.place_tile(msg)
    
    if isinstance(msg,tiles.MessageMoveToken):
        game_master.move_token(msg)

    return

def read_socket(s):
        if s is serversock:
            new_connection(s)
        else:
            try:
                data = s.recv(4096)
            except ConnectionResetError:
                data = 0
            if not data:
                disconnect_client(s)
            elif data:
                process_data(data)
        return
               
def disconnect_client(s):
    # A readable client socket with no data has disconnected
    # print("Server closing {}".format(s.getpeername()))
    global inputs
    global outputs
    global message_queues
    global game_master

    game_master.disconnect_player(s)
    
    if s in outputs:
        outputs.remove(s)
    if s in inputs:
        inputs.remove(s)
    s.close()

    del message_queues[s]
    print("message_queue len {}".format(len(message_queues)))
    return

def debug():
    print("len(inputs) {}".format(len(inputs)))



server_address = ('', 30020)
serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# To make it so that we can reuse the address set option SO_REUSEADDR
serversock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
serversock.bind(server_address)
serversock.listen(ALLOWED_CONNECTIONS)

inputs.append(serversock)

# Creating game master here because I want to give time for all clients to
# connect, which I do using a born time on the game_master
game_master = GameMaster() 
timeout_counter = 0 

# This is the logger to keep track of all the messages that were sent to all.
# Will be used to bring a new spectator up to speed
logger = Logger()

while inputs:
    # wait for at least one of the sockets to be ready for processing
    #print("Server waiting for next event")

    # Check if we can start the game
    if timeout_counter > 2 and not game_master.in_game:
        if len(inputs)-1 >= 2:
            print("Server starting game with {} connections".format(len(inputs)-1))
            game_master.start_game()
        else:
            print("Server doesn't have enough connections to start game")
    elif not game_master.in_game:
        print("timeout_counter: {} in_game: {}".format(timeout_counter,game_master.in_game))
    
    # Check if current player has been taking too long
    current_time = time.perf_counter()
    if current_time - game_master.turn_start_time > MAX_TURN_TIME and game_master.in_game:
        print("current_time {} and turn_start_time {}".format(current_time,game_master.turn_start_time))
        game_master.random_turn()
    

    readable, writable, exceptional = select.select(inputs, outputs, inputs,SELECT_TIMEOUT)

    if not readable and not writable and not exceptional:
        timeout_counter += 1
    else:
        timeout_counter = 0

    for socket in readable:
        read_socket(socket)

    for socket in writable:
        write_socket(socket)
    
    for socket in exceptional:
        handle_socket(socket)