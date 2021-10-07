from hermes import Hermes
import tiles

server_address = ('', 30020)
number_allowed_connections = 20
number_of_players = tiles.PLAYER_LIMIT 
countdown_time = 2

hermes = Hermes(server_address,number_allowed_connections,number_of_players,countdown_time)
hermes.start_server()
#except Exception as err:
    #print("SERVER SHUT DOWN ERROR: {}".format(err))
