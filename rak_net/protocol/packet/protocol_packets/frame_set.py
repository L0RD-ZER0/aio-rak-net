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

from ....frame import Frame
from ..packet import Packet
from ...protocol_info import ProtocolInfo


class FrameSet(Packet):
    """
    A packet consisting of a set of frames.

    :param data: Data of the packet
    :param pos: Read-Write position for the stream
    """
    def __init__(self, data: bytes = b"", pos: int = 0):
        super().__init__(data, pos=pos)
        self.packet_id: int = ProtocolInfo.FRAME_SET
        self.sequence_number: int = 0
        self.frames: list[Frame] = []
  
    def decode_payload(self) -> None:
        """
        Method to decode the payload
        """
        self.sequence_number = self.read_unsigned_triad_le()
        while not self.feos():
            frame: Frame = Frame(self.data[self.pos:])
            frame.decode()
            self.frames.append(frame)
            self.pos += frame.size
        
    def encode_payload(self) -> None:
        """
        Method to encode the payload
        """
        self.write_unsigned_triad_le(self.sequence_number)
        for frame in self.frames:
            frame.encode()
            self.write(frame.data)

    @property
    def size(self) -> int:
        """
        Size of the frame set
        :return: Size of the frame set
        """
        return self._get_size()

    def _get_size(self) -> int:
        """
        Function to get the size of a frame set
        :return: size of a frame set
        """
        length: int = 4
        for frame in self.frames:
            length += frame.size
        return length
