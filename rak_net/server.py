from __future__ import annotations
import sys
import time
from asyncio import Lock as _Lock, AbstractEventLoop as _AbstractEventLoop, get_event_loop, sleep, gather
from random import randint
from .utils import InternetAddress
from .socket import AsyncUDPSocket
from .connection import Connection
from .protocol import Handler, ProtocolInfo


__all__ = 'Server',


class Server:
    """
    Rak-Net Server interface.
    All raknet servers must be an instance of this class.

    :param protocol_version: Protocol Version for Rak-Net
    :param hostname: Hostname for the server
    :param port: Port for the server
    :param ipv: IP-Version for the server
    :param tps: Ticks-Per-Second of the server
    :param lock: Lock for protecting resources, is an instance of :class:`asyncio.Lock`. In case it is not provided, a new instance would be created
    :param loop: Asyncio-Loop for the server, in case no loop is provided, :func:`asyncio.get_event_loop` would be used to obtaun the event loop
    """
    def __init__(self, protocol_version: int, hostname: str, port: int, *, ipv: int = 4, tps: int = 100, lock: _Lock = None, loop: _AbstractEventLoop = None):
        self.tick_sleep_time: float = 1/tps
        self.protocol_version: int = protocol_version
        """Protocol-Version of the server"""
        self.address: InternetAddress = InternetAddress(hostname, port, ipv)
        """:class:`InternetAddress` of the server"""
        self.guid: int = randint(0, sys.maxsize,)
        """GUID of the server"""
        self.socket: AsyncUDPSocket = AsyncUDPSocket(True, ipv, hostname, port, loop=loop)
        """Socket within the server"""
        self.connections: dict[str, Connection] = {}
        self.start_time: int = int(time.time() * 1000)
        """Start-Time of the server"""
        self._loop = loop if loop is not None else get_event_loop()
        self._lock: _Lock = lock if lock is not None else _Lock()
        self.handler = Handler(self)
        """:class:`Handler` for the server"""
        self.socket.prime(self.address.hostname, self.address.port)

    def get_time_ms(self) -> int:
        """
        Get the time elapsed since server started in miliseconds
        :return: Returns the time elapsed (in miliseconds) since server staretd
        """
        return int(time.time() * 1000) - self.start_time

    async def add_connection(self, address: InternetAddress, mtu_size: int) -> None:
        """
        Method to add a connection to the server

        :param address: :class:`InternetAddress` on which to add a connection
        :param mtu_size:  MTU-Size of the connection
        """
        async with self._lock:
            self.connections[address.token] = Connection(address, mtu_size, self)

    async def remove_connection(self, address: InternetAddress) -> Connection:
        """
        Method to remove the connection form the server

        :param address: :class:`InternetAddress` of the connection to be removed
        :return: :class:`Connection` removed from the server
        """
        async with self._lock:
            return self.connections.pop(address.token)

    async def get_connection(self, address: InternetAddress) -> Connection | None:
        """
        Method to get a running connection from the server

        :param address: Address for which to get the connection
        :return: A :class:`Connection` if it exists, else `None`
        """
        async with self._lock:
            return self.connections.get(address.token, None)

    async def send_data(self, data: bytes, address: InternetAddress) -> None:
        """
        Method to send data to an :class:`InternetAddress`

        :param data: Data to be sent
        :param address: Address to which the data is to be sent
        """
        return await self.socket.send(data, address.hostname, address.port)

    async def tick(self) -> None:
        """
        Method representing a `tick`
        """
        for connection in dict(self.connections).values():
            await gather(connection.update())

    async def _handle(self) -> None:
        recv: tuple = await self.socket.recieve()
        if recv[0]:
            address: InternetAddress = InternetAddress(recv[1][0], recv[1][1])
            if address.token in self.connections:
                await (await self.get_connection(address)).handle(recv[0])
            elif recv[0][0] in [ProtocolInfo.OFFLINE_PING, ProtocolInfo.OFFLINE_PING_OPEN_CONNECTIONS]:
                data = await self.handler.handle_offline_ping(recv[0], address)
                await self.send_data(data, address)
            elif recv[0][0] == ProtocolInfo.OPEN_CONNECTION_REQUEST_1:
                data = await self.handler.handle_open_connection_request_1(recv[0])
                await self.send_data(data, address)
            elif recv[0][0] == ProtocolInfo.OPEN_CONNECTION_REQUEST_2:
                data = await self.handler.handle_open_connection_request_2(recv[0], address)
                await self.send_data(data, address)

    async def start(self) -> None:
        """
        Coroutine to start a handle-Loop for the server
        """
        while True:
            await self._handle()
            await sleep(self.tick_sleep_time)

    def run(self) -> None:
        """
        Method to run the server. Blocks the IO.
        """
        return self._loop.run_until_complete(self.start())
