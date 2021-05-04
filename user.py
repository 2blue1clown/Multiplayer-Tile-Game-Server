class User:
    def __init__(self, name, connection,game_master):
        self.name = name
        self.connection = connection
        self.game_master = game_master
        self.idnum = 0

    def become_player(self):
        return Player(self.name,self.connection,self.game_master)

class Player(User):
    def __init__(self, name, connection,game_master):
        super().__init__(name,connection,game_master)
        self.placed_token = False
        self.idnum = self.game_master.free_id()
    
    def become_user(self):
        return User(self.name, self.connection,self.game_master)
