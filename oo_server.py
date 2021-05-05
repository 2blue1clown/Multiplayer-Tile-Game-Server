from hermes import Hermes
import game_master

server_address = ('', 30020)
number_allowed_connections = 5
number_of_players = 2

hermes = Hermes(server_address,number_allowed_connections,number_of_players)
hermes.start_server()
#try:
    #hermes.start_server()
#except Exception as err:
    #print("SERVER STOPPING ERROR: {}".format(err))
#try:
    #hermes.shut_down()
#except Exception as err:
    #print("SERVER SHUT DOWN ERROR: {}".format(err))
