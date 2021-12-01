from __future__ import annotations
from binary_utils.binary_stream import binary_stream
from .utils import ReliabilityTool

__all__ = 'Frame',


class Frame(binary_stream):
    """
    Binary stream for a Frame object

    :param data: Data of the frame
    :param pos: Read/Write position of the frame
    :param reliability: Reliability-integer of the frame
    :param fragmented: Boolean depicting whether frame is fragmented or not
    :param reliable_frame_index: Reliability frame index of the frame
    :param sequenced_frame_index: Sequenced frame index of the frame
    :param ordered_frame_index: Ordered frame index of the frame
    :param order_channel: Order channel of the frame
    :param compound_size: Compound-Size of the frame
    :param compound_id: Compound-ID of the frame
    :param index: Index of the frame
    :param body: Body of the frame
    """

    def __init__(self,
                 data: bytes = b'',
                 *, pos: int = 0,
                 reliability: int = 0,
                 fragmented: bool = False,
                 reliable_frame_index: int = 0,
                 sequenced_frame_index: int = 0,
                 ordered_frame_index: int = 0,
                 order_channel: int = 0,
                 compound_size: int = 0,
                 compound_id: int = 0,
                 index: int = 0,
                 body: bytes = b''
                 ):
        super().__init__(data, pos)
        self.data: bytes
        """Data of the frame"""
        self.pos: int
        """Read/Write position of the frame"""
        self.reliability: int = reliability
        """Reliability-integer of the frame"""
        self.fragmented: bool = fragmented
        """Boolean depicting whether frame is fragmented or not"""
        self.reliable_frame_index: int = reliable_frame_index
        """Reliability frame index of the frame"""
        self.sequenced_frame_index: int = sequenced_frame_index
        """Sequenced frame index of the frame"""
        self.ordered_frame_index: int = ordered_frame_index
        """Ordered frame index of the frame"""
        self.order_channel: int = order_channel
        """Order channel of the frame"""
        self.compound_size = compound_size
        """Compound-Size of the frame"""
        self.compound_id = compound_id
        """Compound-ID of the frame"""
        self.index = index
        """Index of the frame"""
        self.body = body
        """Body of the frame"""

    def decode(self) -> None:
        """
        Method to decode the frame
        """
        flags: int = self.read_unsigned_byte()
        self.reliability = (flags & 0xf4) >> 5
        self.fragmented = (flags & 0x10) > 0
        body_length: int = self.read_unsigned_short_be() >> 3
        if ReliabilityTool.reliable(self.reliability):
            self.reliable_frame_index = self.read_unsigned_triad_le()
        if ReliabilityTool.sequenced(self.reliability):
            self.sequenced_frame_index = self.read_unsigned_triad_le()
        if ReliabilityTool.sequenced_or_ordered(self.reliability):
            self.ordered_frame_index = self.read_unsigned_triad_le()
            self.order_channel = self.read_unsigned_byte()
        if self.fragmented:
            self.compound_size = self.read_unsigned_int_be()
            self.compound_id = self.read_unsigned_short_be()
            self.index = self.read_unsigned_int_be()
        self.body = self.read(body_length)

    def encode(self) -> None:
        """
        Method to encode the frame
        """
        self.write_unsigned_byte((self.reliability << 5) | (0x10 if self.fragmented else 0))
        self.write_unsigned_short_be(len(self.body) << 3)
        if ReliabilityTool.reliable(self.reliability):
            self.write_unsigned_triad_le(self.reliable_frame_index)
        if ReliabilityTool.sequenced(self.reliability):
            self.write_unsigned_triad_le(self.sequenced_frame_index)
        if ReliabilityTool.sequenced_or_ordered(self.reliability):
            self.write_unsigned_triad_le(self.ordered_frame_index)
            self.write_unsigned_byte(self.order_channel)
        if self.fragmented:
            self.write_unsigned_int_be(self.compound_size)
            self.write_unsigned_short_be(self.compound_id)
            self.write_unsigned_int_be(self.index)
        self.write(self.body)

    @property
    def size(self):
        """Size of the frame"""
        return self._get_size()

    def _get_size(self) -> int:
        """Method to get size of the frame"""
        length: int = 3
        if ReliabilityTool.reliable(self.reliability):
            length += 3
        if ReliabilityTool.sequenced(self.reliability):
            length += 3
        if ReliabilityTool.sequenced_or_ordered(self.reliability):
            length += 4
        if self.fragmented:
            length += 10
        length += len(self.body)
        return length
