import hermes

# This is a class whose job is to keep a log of all of the messages that have been sent
# to all clients, so that new spectator clients can catch up to the game.

class Logger():
    def __init__(self, hermes):
        self.log = [] # this is the log of messages with index 0 being the earliest message
        self.hermes = hermes

    # add a messge to the log   
    def add(self, msg):
        self.log.append(msg)

    # used on new spectator clients to bring them up to the current game turn 
    def update_client(self,client_connection):
        for msg in self.log:
            self.hermes.send_to(msg,client_connection)
        print("Updating {}".format(client_connection.getpeername()))
    

