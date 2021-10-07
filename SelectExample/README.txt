This is a small example of using select() to manage multiple client connections in a server.

You might find select() to be more effective than threading for the project, because
there are few client connections involved in our server, and it is much simpler to
reason about the behaviour of a single-threaded server using select().

To try the example, run the server using:
  python3 server.py

And run a couple of clients using:
  python3 client.py

You should see a message on the server each time a client connects, e.g.:
  received connection from ('127.0.0.1', 51012)

Type some text into one of the clients and press enter. You should see the text printed on the server:
  ('127.0.0.1', 51016): hello

You should also see the same message printed back on all connected clients.

Read through the comments in the server.py code, and you should be able to see
how it handles receiving messages from all of the connected clients, as well
as sending messages to all connected clients.

Consider whether or not it might be easier, for yourself, to manage and
synchronise the Tiles game using this approach.
