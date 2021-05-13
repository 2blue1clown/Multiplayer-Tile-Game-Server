import hermes

class User:
    def __init__(self, name, connection,game_master,hermes):
        self.name = name
        self.connection = connection
        self.game_master = game_master
        self.idnum = 0
        self.hermes = hermes

        if type(self) == User:
            self.hermes.make_silent(self.connection)
        elif type(self) == Player:
            self.hermes.make_input(self.connection)
    

    def become_player(self):
        return Player(self.name,self.connection,self.game_master,self.hermes)

class Player(User):
    def __init__(self, name, connection,game_master,hermes):
        super().__init__(name,connection,game_master,hermes)
        self.placed_token = False
        self.idnum = self.game_master.free_id()
    
    def become_user(self):
        return User(self.name, self.connection,self.game_master,self.hermes)
