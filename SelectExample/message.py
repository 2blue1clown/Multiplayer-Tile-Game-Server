import struct

class Message:
  def __init__(self, contents: str):
    self.contents = contents
  
  def pack(self):
    contentsbytes = bytes(self.contents, 'utf-8')
    contentslen = len(contentsbytes)
    return struct.pack('!L{}s'.format(contentslen), contentslen, contentsbytes)
  
  @classmethod
  def unpack(cls, bs: bytearray):
    headerlen = struct.calcsize('!L')
    
    if len(bs) >= headerlen:
      contentslen, = struct.unpack_from('!L', bs, 0)
      if len(bs) >= headerlen + contentslen:
        contentsbytes, = struct.unpack_from('!{}s'.format(contentslen), bs, headerlen)
        contents = contentsbytes.decode('utf-8')
        return Message(contents), headerlen + contentslen
    
    return None, 0
