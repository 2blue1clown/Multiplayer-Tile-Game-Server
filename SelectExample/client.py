from os import read
import socket
import sys
import threading
import message

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host = 'localhost'
server_address = (server_host, 30021)
sock.connect(server_address)
sock.setblocking(True)

def user_input_thread():
  for line in sys.stdin:
    line = line.strip()
    if line:
      msg = message.Message(line)
      sock.sendall(msg.pack())

input_thread = threading.Thread(target=user_input_thread, daemon=True)
input_thread.start()

buffer = bytearray()

while True:
  chunk = sock.recv(4096)
  if chunk:
    buffer.extend(chunk)
    while True:
      msg, consumed = message.Message.unpack(buffer)
      if consumed:
        buffer = buffer[consumed:]
        print(msg.contents)
      else:
        break
  else:
    break
