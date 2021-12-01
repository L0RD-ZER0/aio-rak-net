################################################################################
#                                                                              #
#  ____           _                                                            #
# |  _ \ ___   __| |_ __ _   _ _ __ ___                                        #
# | |_) / _ \ / _` | '__| | | | '_ ` _ \                                       #
# |  __/ (_) | (_| | |  | |_| | | | | | |                                      #
# |_|   \___/ \__,_|_|   \__,_|_| |_| |_|                                      #
#                                                                              #
# Copyright 2021 Podrum Studios                                                #
#                                                                              #
# Permission is hereby granted, free of charge, to any person                  #
# obtaining a copy of this software and associated documentation               #
# files (the "Software"), to deal in the Software without restriction,         #
# including without limitation the rights to use, copy, modify, merge,         #
# publish, distribute, sublicense, and/or sell copies of the Software,         #
# and to permit persons to whom the Software is furnished to do so,            #
# subject to the following conditions:                                         #
#                                                                              #
# The above copyright notice and this permission notice shall be included      #
# in all copies or substantial portions of the Software.                       #
#                                                                              #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR   #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,     #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER       #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING      #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS #
# IN THE SOFTWARE.                                                             #
#                                                                              #
################################################################################

from ..packet import Packet
from ...protocol_info import ProtocolInfo


class OfflinePing(Packet):
    """
    A packet representing an Offline-Ping

    :param data: Data of the packet
    :param pos: Read-Write position for the stream
    """
    def __init__(self, data: bytes = b"", pos: int = 0):
        super().__init__(data, pos=pos)
        self.packet_id: int = ProtocolInfo.OFFLINE_PING
        self.client_timestamp: int = 0
        self.magic: bytes = b""
        self.client_guid: int = 0
  
    def decode_payload(self) -> None:
        """
        Method to encode the payload
        """
        self.client_timestamp = self.read_unsigned_long_be()
        self.magic = self.read(16)
        if not self.feos():
            self.client_guid = self.read_unsigned_long_be()
        
    def encode_payload(self) -> None:
        """
        Method to encode the payload
        """
        self.write_unsigned_long_be(self.client_timestamp)
        self.write(self.magic)
        self.write_unsigned_long_be(self.client_guid)
