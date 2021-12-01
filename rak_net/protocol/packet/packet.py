from __future__ import annotations
from socket import AF_INET6, inet_pton, inet_ntop
from binary_utils import binary_stream
from ...utils import InternetAddress


__all__ = 'Packet',


class Packet(binary_stream):
    """
    Base-Class for Packets
    All packets are supposed to inherit from this class

    :param data: Data of the packet
    :param pos: Read-Write position for the stream
    """

    def __init__(self, data: bytes = b"", *, pos: int = 0):
        super().__init__(data, pos)
        self.packet_id: int = 0

    def decode_header(self) -> None:
        """
        Method to decode the packet's header
        """
        self.pos += 1

    def decode(self) -> None:
        """
        Method to decode the packet
        """
        self.decode_header()
        if hasattr(self, "decode_payload"):
            self.decode_payload()

    def encode_header(self) -> None:
        """
        Method to encode the packet's header
        """
        self.write_unsigned_byte(self.packet_id)

    def encode(self) -> None:
        """
        Method to encode the packet
        """
        self.encode_header()
        if hasattr(self, "encode_payload"):
            self.encode_payload()

    def read_address(self) -> InternetAddress:
        """
        Method to read the address from the packet

        :return: Instance of :class:`InternetAddress` containing address from the packet
        """
        version: int = self.read_unsigned_byte()
        if version == 4:
            hostname_parts: list = []
            for i in range(0, 4):
                hostname_parts.append(str(~self.read_unsigned_byte() & 0xff))
            hostname: str = ".".join(hostname_parts)
            port: int = self.read_unsigned_short_be()
            return InternetAddress(hostname, port, version)
        if version == 6:
            self.read_unsigned_short_le()
            port: int = self.read_unsigned_short_be()
            self.read_unsigned_int_be()
            hostname: str = inet_ntop(AF_INET6, self.read(16))
            self.read_unsigned_int_be()
            return InternetAddress(hostname, port, version)

    def write_address(self, address: InternetAddress) -> None:
        """
        Method to write an :class:`InternetAddress` to the packet.

        :param address: Address to be written
        """
        if address.version == 4:
            self.write_unsigned_byte(address.version)
            hostname_parts: list = address.hostname.split(".")
            for part in hostname_parts:
                self.write_unsigned_byte(~int(part) & 0xff)
            self.write_unsigned_short_be(address.port)
        elif address.version == 6:
            self.write_unsigned_byte(address.version)
            self.write_unsigned_short_le(AF_INET6)
            self.write_unsigned_short_be(address.port)
            self.write_unsigned_int_be(0)
            self.write(inet_pton(AF_INET6, address.hostname))
            self.write_unsigned_int_be(0)

    def read_string(self) -> str:
        """
        Method to read a string from packet

        :return: The string read from the packet
        """
        return self.read(self.read_unsigned_short_be()).decode()

    def write_string(self, value: str) -> None:
        """
        Method to write a method to the packet

        :param value: The string to be written to the packet
        """
        self.write_unsigned_short_be(len(value))
        self.write(value.encode())
