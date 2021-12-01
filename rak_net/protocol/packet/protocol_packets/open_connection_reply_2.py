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
from ....utils.internet_address import InternetAddress


class OpenConnectionReply2(Packet):
    """
    One of the packets for Open-Connection-Reply

    :param data: Data of the packet
    :param pos: Read-Write position for the stream
    """

    def __init__(self, data: bytes = b"", pos: int = 0) -> None:
        super().__init__(data, pos)
        self.packet_id: int = ProtocolInfo.OPEN_CONNECTION_REPLY_2
        self.magic: bytes = b""
        self.server_guid: int = 0
        self.client_address: InternetAddress = InternetAddress("255.255.255.255", 0)
        self.mtu_size: int = 0
        self.use_encryption: bool = False
  
    def decode_payload(self) -> None:
        """
        Method to decode the payload
        """
        self.magic = self.read(16)
        self.server_guid = self.read_unsigned_long_be()
        self.client_address = self.read_address()
        self.mtu_size = self.read_unsigned_short_be()
        self.use_encryption = self.read_bool()
        
    def encode_payload(self) -> None:
        """
        Method to encode the payload
        """
        self.write(self.magic)
        self.write_unsigned_long_be(self.server_guid)
        self.write_address(self.client_address)
        self.write_unsigned_short_be(self.mtu_size)
        self.write_bool(self.use_encryption)
