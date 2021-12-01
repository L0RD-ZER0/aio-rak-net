from __future__ import annotations
from typing import TYPE_CHECKING
from .packet import (
    ConnectionRequest,
    ConnectionRequestAccepted,
    NewIncomingConnection,
    OfflinePing,
    OfflinePong,
    OnlinePing,
    OnlinePong,
    OpenConnectionRequest1,
    OpenConnectionReply1,
    OpenConnectionRequest2,
    OpenConnectionReply2,
    IncompatibleProtocolVersion,
)
from .protocol_info import ProtocolInfo
from ..utils import InternetAddress
if TYPE_CHECKING:
    from ..server import Server

__all__ = 'Handler',


class Handler:
    """
    Class containing various handler methods to handle packets

    :param server: Server for which handler is intended
    """

    __slots__ = 'server',

    def __init__(self, server: Server):
        self.server = server

    async def handle_connection_request(self, data: bytes, address: InternetAddress, *, server: Server = None) -> bytes:
        """
        Handler to handle `Connection-Request`

        :param data: data of the packet
        :param address: :class:`InternetAddress` of the packet
        :param server: Optional server to use the handler with, defaults to ``self.handler``
        :return: returns the processed data
        """
        server = server or self.server
        packet: ConnectionRequest = ConnectionRequest(data)
        packet.decode()
        new_packet: ConnectionRequestAccepted = ConnectionRequestAccepted()
        new_packet.client_address = address
        new_packet.system_index = 0
        new_packet.server_guid = server.guid
        new_packet.system_addresses = [InternetAddress("255.255.255.255", 19132)] * 20
        new_packet.request_timestamp = server.get_time_ms()
        new_packet.encode()
        return new_packet.data

    async def handle_connection_request_accepted(self, data: bytes, address: InternetAddress, *, server: Server = None) -> bytes:
        """
        Handler to handle `Connection-Request-Accepted`

        :param data: data of the packet
        :param address: :class:`InternetAddress` of the packet
        :param server: Optional server to use the handler with, defaults to ``self.handler``
        :return: returns the processed data
        """
        server = server or self.server
        packet: ConnectionRequestAccepted = ConnectionRequestAccepted(data)
        packet.decode()
        new_packet: NewIncomingConnection = NewIncomingConnection()
        new_packet.server_address = address
        new_packet.system_addresses = packet.system_addresses
        new_packet.request_timestamp = packet.accepted_timestamp
        new_packet.accepted_timestamp = server.get_time_ms()
        new_packet.encode()
        return new_packet.data

    async def handle_offline_ping(self, data: bytes, address: InternetAddress = None, *, server: Server = None) -> bytes:
        """
        Handler to handle `Offline-Ping`

        :param data: data of the packet
        :param address: :class:`InternetAddress` of the packet
        :param server: Optional server to use the handler with, defaults to ``self.handler``
        :return: returns the processed data
        """
        server = server or self.server
        packet: OfflinePing = OfflinePing(data)
        packet.decode()
        new_packet: OfflinePong = OfflinePong()
        new_packet.client_timestamp = packet.client_timestamp
        new_packet.server_guid = server.guid
        new_packet.magic = ProtocolInfo.MAGIC
        new_packet.server_name = server.name if hasattr(server, "name") else ""
        new_packet.encode()
        return new_packet.data

    async def handle_online_ping(self, data: bytes, address: InternetAddress = None, *, server: Server = None) -> bytes:
        """
        Handler to handle `Online-Ping`

        :param data: data of the packet
        :param address: :class:`InternetAddress` of the packet
        :param server: Optional server to use the handler with, defaults to ``self.handler``
        :return: returns the processed data
        """
        server = server or self.server
        packet: OnlinePing = OnlinePing(data)
        packet.decode()
        new_packet: OnlinePong = OnlinePong()
        new_packet.client_timestamp = packet.client_timestamp
        new_packet.server_timestamp = server.get_time_ms()
        new_packet.encode()
        return new_packet.data

    async def handle_open_connection_request_1(self, data: bytes, address: InternetAddress = None, *, server: Server = None) -> bytes:
        """
        Handler to handle `Open-Connection-Request-1`

        :param data: data of the packet
        :param address: :class:`InternetAddress` of the packet
        :param server: Optional server to use the handler with, defaults to ``self.handler``
        :return: returns the processed data
        """
        server = server or self.server
        packet: OpenConnectionRequest1 = OpenConnectionRequest1(data)
        packet.decode()
        if packet.protocol_version == server.protocol_version:
            new_packet: OpenConnectionReply1 = OpenConnectionReply1()
            new_packet.magic = ProtocolInfo.MAGIC
            new_packet.server_guid = server.guid
            new_packet.use_security = False
            new_packet.mtu_size = packet.mtu_size
        else:
            new_packet: IncompatibleProtocolVersion = IncompatibleProtocolVersion()
            new_packet.protocol_version = server.protocol_version
            new_packet.magic = ProtocolInfo.MAGIC
            new_packet.server_guid = server.guid
        new_packet.encode()
        return new_packet.data

    async def handle_open_connection_request_2(self, data: bytes, address: InternetAddress = None, *, server: Server = None) -> bytes:
        """
        Handler to handle `Open-Connection-Request-2`

        :param data: data of the packet
        :param address: :class:`InternetAddress` of the packet
        :param server: Optional server to use the handler with, defaults to ``self.handler``
        :return: returns the processed data
        """
        server = server or self.server
        packet: OpenConnectionRequest2 = OpenConnectionRequest2(data)
        packet.decode()
        new_packet: OpenConnectionReply2 = OpenConnectionReply2()
        new_packet.magic = ProtocolInfo.MAGIC
        new_packet.server_guid = server.guid
        new_packet.client_address = address
        new_packet.mtu_size = packet.mtu_size
        new_packet.use_encryption = False
        new_packet.encode()
        await server.add_connection(address, packet.mtu_size)
        return new_packet.data
