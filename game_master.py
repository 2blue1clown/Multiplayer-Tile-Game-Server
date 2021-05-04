import random
import hermes #this is my messenger/server class
import tiles
import user
import time




class GameMaster():

    def __init__(self, hermes, number_of_players):
        self.board = tiles.Board()
        self.number_of_players = number_of_players
        
        self.users = [ ]  # Users that are not players are spectators. Players will never be users
        self.players = {} #This will start empty. The key for a player will be the idnum
        self.player_order = []

        self.hermes = hermes #TODO should hermes make game_master or vice versa
        self.is_started = False #TODO should be used by hermes

    
    def welcome(self,connection, client_address):
        host, port = client_address
        name = '{}:{}'.format(host, port)

        new_user = user.User(name,connection,self)
        self.users.append(new_user)
        print("GM: added user")

        self.hermes.send_to(tiles.MessageWelcome(new_user.idnum).pack(),new_user.connection)

        print("GM: len(users) is: {} number_of_players is: {}".format(len(self.users),self.number_of_players))

        #TODO change the start game conditions
        if(len(self.users) >= self.number_of_players):
            
            self.start_game()

    def rewelcome(self):
        for user in self.users:
            print('GM: rewelcoming: {}'.format(user.name))
            self.hermes.send_to(tiles.MessageWelcome(user.idnum).pack(),user.connection)
    
    def free_id(self):
        if(len(self.players)>=4):
            raise Exception("GM: Too many players")
        for idnum in range(self.number_of_players):
            if idnum not in self.players.keys():
                break
        return idnum

    def pick_players(self):
        while len(self.players) < self.number_of_players:
            index = random.randint(0,len(self.users)-1)
            chosen_user = self.users.pop(index)
            chosen_user = chosen_user.become_player()
            self.players[chosen_user.idnum] = chosen_user

        
    def start_game(self):
        self.pick_players() #this will determine who joins the game and who is a spectator

        print('Starting player idnums:',self.players.keys()) 

        # players all start with token_placed = False

        #send player tiles 
        for player in self.players.values():  
            self.hermes.send_to(tiles.MessageWelcome(player.idnum).pack(),player.connection)
            self.hermes.send_all(tiles.MessagePlayerJoined(player.name,player.idnum).pack())
            
        #send a start game message (this sends to all connections regardless of user or player status)
        self.hermes.send_all(tiles.MessageGameStart().pack())

        # send all players their tiles
        for player in self.players.values():
            for _ in range(tiles.HAND_SIZE):
                tileid = tiles.get_random_tileid()
                self.hermes.send_to(tiles.MessageAddTileToHand(tileid).pack(),player.connection)

        self.first_turn = True
        # set player order.
        for player in self.players.values():
            self.player_order.append(player)
        self.next_turn()

    #next_turn will check if the game is finished as well
    def next_turn(self): 
        if(self.is_finished()):
            self.finish_game()       
        else:
            #check if this is the first tern of the game
            if self.first_turn:
                next_player = self.player_order.pop(0)
                self.player_order.append(next_player)
                print("GM: Player {} goes first".format(next_player.idnum))
                self.first_turn = False
            #check if the previous turn's player has placed their token
            elif self.player_order[-1].placed_token:
                next_player = self.player_order.pop(0)
                self.player_order.append(next_player)
                print("GM: Sent next turn to {}".format(next_player))
            else:
                next_player = self.player_order[-1] # current player
                print("GM: Player {} gets another turn".format(next_player))

            self.hermes.send_all(tiles.MessagePlayerTurn(next_player.idnum).pack())

    def change_player_to_user(self, idnum):
        print("GM: Player {} eliminated".format(idnum))
        try:
            elim_player = self.players.pop(idnum)
            self.player_order.remove(elim_player)
            elim_player = elim_player.become_user()
            self.users.append(elim_player)
        except KeyError:
            return


    def do_eliminations(self,eliminated):
        # need to check for any eliminations
        for idn in eliminated:
            if idn in self.players.keys():#players.keys() is all the player idnums

                self.hermes.send_all(tiles.MessagePlayerEliminated(idn).pack())
                self.change_player_to_user(idn)



    def place_tile(self,msg):

        if self.board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
            print("GM: tile placed by {}".format(msg.idnum))
            msg_player = self.players[msg.idnum]
            # notify client that placement was successful
            self.hermes.send_all(msg.pack())
            # check for token movement
            positionupdates, eliminated = self.board.do_player_movement(self.players.keys())

            for msg in positionupdates:
                self.hermes.send_all(msg.pack())
            
            # check and send messages for eliminations
            self.do_eliminations(eliminated)
                
            # pickup a new tile
            tileid = tiles.get_random_tileid()
            self.hermes.send_to(tiles.MessageAddTileToHand(tileid).pack(),msg_player.connection)
            print("GM: tile sent to {}".format(msg_player.idnum))

            # start next turn 
            self.next_turn()

    def move_token(self,msg):
        if not self.board.have_player_position(msg.idnum):
            if self.board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
                print("GM: token moved by {}".format(msg.idnum))
                msg_player = self.players[msg.idnum]

                # Keep a track of whether or not we have a placed token
                msg_player.placed_token = True

                # check for token movement
                positionupdates, eliminated = self.board.do_player_movement(self.players.keys())

                for msg in positionupdates:
                    self.hermes.send_all(msg.pack())
                
                # need to check for any eliminations
                self.do_eliminations(eliminated)
                
                # start next turn
                self.next_turn()
    
    # to be used by hermes to let the game know when a client disconnected
    def remove_client(self,connection):
        for player in self.players.values():
            if player.connection is connection:
                #need to eliminate player
                self.players.pop(player.idnum)
                self.hermes.send_all(tiles.MessagePlayerEliminated(player.idnum).pack())
                return
        for user in self.users:
            if user.connection is connection:
                self.users.remove(user)
                return

    def is_finished(self):
        print('GM: len(players): {}'.format(len(self.players)))
        if len(self.players)<2:
            return True
        else:
            return False

    def finish_game(self):
        print('GM: Game is finished')
        for idnum in range(0,self.number_of_players):
            self.change_player_to_user(idnum)
        
        print('GM: Sending countdown before next game')

        self.hermes.send_all(tiles.MessageCountdown().pack())

        time.sleep(5) #TODO change this be more easily adjustable.
        self.is_started = False
        print('GM: Current users: {}'.format(self.users))

        self.board = tiles.Board()
        #Send new welcome messages to the user
        self.rewelcome()
        self.start_game()
        

        
#TODO
# need to make it so that it gracefully exits when a client disconnects
# need to fix the but where if at the start of the game player 1 eliminates themselves then
# the second player is told they are a winner when they are not. (maybe do a forced cycle through
# the turn order?)
# need to make is so that when the game finishes the screen is still updated and the winner is told 
# they won 
# 
            
        
