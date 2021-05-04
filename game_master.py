import random
import hermes #this is my messenger/server class
import tiles





class GameMaster():

    def __init__(self, hermes, number_of_players,):
        self.board = tiles.Board()
        self.number_of_players = number_of_players
        
        self.names = {} #used in start game to let clients know who is playing the game
        self.connections = {} # links idnum to the connection
        self.placed_token = {} #use the idnum to determine if the player has placed a token
        self.live_idnums = [] #this will also be used for turn order
        self.spectator_idnums = []
        self.hermes = hermes #TODO should hermes make game_master or vice versa
        self.is_started = False
    
    def welcome(self,connection, client_address):
        host, port = client_address
        name = '{}:{}'.format(host, port)

        idnum = self.free_id()
        self.spectator_idnums.append(idnum) # everyone starts as a spectator
        self.names[idnum] = name
        self.connections[idnum] = connection
        self.hermes.send_to(tiles.MessageWelcome(idnum).pack(),self.connections[idnum])

        if(len(self.spectator_idnums) >= self.number_of_players):
            self.start_game()
    
    def free_id(self):
        if (len(self.spectator_idnums) > 0) or (len(self.live_idnums) > 0):
            new_id = max(max(self.live_idnums,self.spectator_idnums))+1
        else:
            new_id = 0
        return new_id

    def pick_players(self):
        while len(self.live_idnums) < self.number_of_players:
            index = random.randint(0,len(self.spectator_idnums)-1)
            self.live_idnums.append(self.spectator_idnums.pop(index))

        
    def start_game(self):
        self.pick_players() #this will determine who joins the game and who is a spectator

        print('Starting live_idnums:',self.live_idnums) 

        #send player tiles and set placed_token to false
        for idnum in self.live_idnums:  
            self.hermes.send_all(tiles.MessagePlayerJoined(self.names[idnum], idnum).pack())
            self.placed_token[idnum] = False

        #send a start game message
        self.hermes.send_all(tiles.MessageGameStart().pack())

        # send all players their tiles
        for idnum in self.live_idnums:
            for _ in range(tiles.HAND_SIZE):
                tileid = tiles.get_random_tileid()
                self.hermes.send_to(tiles.MessageAddTileToHand(tileid).pack(),self.connections[idnum])

        self.first_turn = True
        self.next_turn()


    def next_turn(self): #! WHAT HAPPENS WHEN A ALL PLAYERS ARE ELIMINATED? 
        #check if this is the first tern of the game
        if self.first_turn:
            next_player = self.live_idnums.pop(0)
            self.live_idnums.append(next_player)
            print("GM: Player {} goes first".format(next_player))
            self.first_turn = False
        #check if the previous turn's player has placed their token
        elif self.placed_token[self.live_idnums[-1]]:
            next_player = self.live_idnums.pop(0)
            self.live_idnums.append(next_player)
            print("GM: Sent next turn to {}".format(next_player))
        else:
            next_player = self.live_idnums[-1] # current player
            print("GM: Player {} gets another turn".format(next_player))

        self.hermes.send_all(tiles.MessagePlayerTurn(next_player).pack())

    def do_eliminations(self,eliminated):
        # need to check for any eliminations
        for idn in eliminated:
            if idn in self.live_idnums:
                self.hermes.send_all(tiles.MessagePlayerEliminated(idn).pack())
                print("GM: Player {} eliminated".format(idn))
                self.live_idnums.remove(idn)
                self.spectator_idnums.append(idn)


    def place_tile(self,msg):

        if self.board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
            print("GM: tile placed by {}".format(msg.idnum))
            # notify client that placement was successful
            self.hermes.send_all(msg.pack())
            # check for token movement
            positionupdates, eliminated = self.board.do_player_movement(self.live_idnums)

            for msg in positionupdates:
                self.hermes.send_all(msg.pack())
            
            # check and send messages for eliminations
            self.do_eliminations(eliminated)
                
            # pickup a new tile
            tileid = tiles.get_random_tileid()
            self.hermes.send_to(tiles.MessageAddTileToHand(tileid).pack(),self.connections[msg.idnum])
            print("GM: tile sent to {}".format(msg.idnum))

            # start next turn 
            self.next_turn()

    def move_token(self,msg):
        if not self.board.have_player_position(msg.idnum):
            if self.board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
                print("GM: token moved by {}".format(msg.idnum))

                # Keep a track of whether or not we have a placed token
                self.placed_token[msg.idnum] = True

                # check for token movement
                positionupdates, eliminated = self.board.do_player_movement(self.live_idnums)

                for msg in positionupdates:
                    self.hermes.send_all(msg.pack())
                
                # need to check for any eliminations
                self.do_eliminations(eliminated)
                
                # start next turn
                self.next_turn()
        
            
        
