# Author: Jono

# This is a countdown timer class
# Once it times out it will use the function that it is given
import time
import threading

    

class Timer(object):
    def __init__(self, timer_length,func):
        self.timer_length = timer_length
        self.func = func

    def __start(self):
        time.sleep(self.timer_length)
        self.func()
        return

    def start(self):
        thread = threading.Thread(target=self.__start)
        thread.start()
        return


#def hi():
    #print('hi')
    #return

#if __name__ == "__main__":
    #t = Timer(3,hi)
    #t.start()
    #print("I can do other things in the mean time")

