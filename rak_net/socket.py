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

from __future__ import annotations
import socket
from asyncio import (
    AbstractEventLoop as _AbstractEventLoop,
    get_event_loop as _get_event_loop,
    Queue, Event,
    Future as _Future
)


class UdpSocket:
    """
    Legacy UDP-Socket
    """
    def __init__(self, is_server: bool, version: int, hostname: str = "", port: int = 0) -> None:
        self.version: int = version
        if is_server:
            self.hostname: str = hostname
            self.port: int = port
        if version == 4:
            self.socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
        elif version == 6:
            self.socket: socket.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.SOL_UDP)
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        else:
            raise Exception(f"Unknown address version {version}")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if is_server:
            try:
                self.socket.bind((hostname, port))
            except socket.error:
                raise Exception(f"Failed to bind to {str(port)}")
        self.socket.setblocking(False)

    def receive(self) -> tuple:
        try:
            return self.socket.recvfrom(65535)
        except socket.error:
            return b"", ("", 0)

    def send(self, data: bytes, hostname: str, port: int) -> None:
        try:
            self.socket.sendto(data, (hostname, port))
        except socket.error:
            return

    def close(self) -> None:
        self.socket.close()


class AsyncUDPSocket:
    """
    Async UDP-Socket for Rak-Net

    :param is_server: Whether the socket is a server
    :param version: IP-Version of the socket
    :param hostname: Hostname of the socket
    :param port: Port of the socket
    :param loop: Loop on which the socket is created. Uses :func:`asyncio.get_event_loop` in case no loop is provided
    :param queue_size: Size for the internal send queu. 0 represents infinite elements. Defaukts to 0
    """
    def __init__(self, is_server: bool, version: int, hostname: str = "localhost", port: int = 0, *, loop: _AbstractEventLoop = None, queue_size: int = None):
        if loop is None:
            loop = _get_event_loop()
        if queue_size is None:
            queue_size = 0
        self._loop: _AbstractEventLoop = loop
        self._queue: Queue = Queue(queue_size, loop=loop)
        self.version: int = version
        self._closed: bool = False
        self._send_event: Event = Event()
        if is_server:
            self._hostname: str = hostname
            self._port: int = port
        if version == 4:
            self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
        elif version == 6:
            self._socket: socket.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.SOL_UDP)
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        else:
            raise Exception(f"Unknown address version {version}")
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    @property
    def is_closed(self) -> bool:
        """
        Whether the loop is closed or not
        """
        return self._closed

    def prime(self, hostname: str = None, port: int = None) -> None:
        """
        Primer for the socket. Binds the socket and prepares sending loop

        :param hostname: IP-Hostname to which the socket is to be bound
        :param port: IP-Port to which the socket is to be bound
        """
        hostname = hostname if hostname is not None else self._hostname
        port = port if port is not None else self._port
        self._socket.bind((hostname, port))
        self._loop.create_task(self._send_loop())

    def run(self) -> None:
        """
        Method to run the socket. Blocks the IO when called
        """
        self.prime()
        self._loop.run_forever()

    async def recieve(self, *, size: int = 65535) -> tuple:
        """
        Method to recieve the data from the socket

        :param size: Size of data to be recieved. Defaults to 65535
        :return: Returns a tuple of data and address in format ``(`data`, (`hostname`, `port`))``
        """
        try:
            return await self._loop.run_in_executor(None, self._socket.recvfrom, size)
        except socket.error:
            return b'', ('', 0)

    async def send(self, data: bytes, hostname: str = "localhost", port: int = 0) -> None:
        """
        Method for sending data to a host and port

        :param data: Data to be sent
        :param hostname: Host to which the data is to eb sent
        :param port: port to which the data is to be sent to
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Data should be of type `bytes` or `bytesarray`")
        await self._queue.put((data, (hostname, port)))
        self._send_event.set()

    def _socket_send(self, data: bytes, address: tuple[str, int], future: _Future = None, registered: bool = False):
        descriptor = self._socket.fileno()
        if future is None:
            future = self._loop.create_future()
        if registered:
            self._loop.remove_writer(descriptor)
        if data:
            try:
                bytes_sent = self._socket.sendto(data, address)
            except (BlockingIOError, InterruptedError):
                self._loop.add_writer(descriptor, self._socket_send, data, address, future, True)
            except Exception as e:
                future.set_exception(e)
                # Socket Error
            else:
                future.set_result(bytes_sent)
        else:
            future.set_result(None)
        return future

    async def _send_loop(self):
        while True:
            await self._send_event.wait()
            try:
                while self._queue.qsize():
                    data, address = await self._queue.get()
                    await self._socket_send(data, address)
            finally:
                self._send_event.clear()

    async def close(self) -> None:
        """
        Method for closing the socket
        """
        self._closed = True
        self._socket.close()


# Spur of moment tests, not meant for production
#
# class AsyncUDPSocket2:
#     def __init__(self, is_server: bool, version: int, hostname: str = "localhost", port: int = 0, *, loop: _AbstractEventLoop = None, queue_size: int = None):
#         if loop is None:
#             loop = _get_event_loop()
#         self._loop: _AbstractEventLoop = loop
#         self.version: int = version
#         self._closed: bool = False
#         if is_server:
#             self._hostname: str = hostname
#             self._port: int = port
#         if version == 4:
#             self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
#         elif version == 6:
#             self._socket: socket.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.SOL_UDP)
#             self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
#         else:
#             raise Exception(f"Unknown address version {version}")
#         self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#
#         self.bind = self._socket.bind
#
#     @property
#     def is_closed(self) -> bool:
#         return self._closed
#
#     async def recieve(self, *, size: int = 65535):
#         return await self._loop.sock_recv(self._socket, size)
#
#
#     async def send(self, data: bytes, hostname: str = "localhost", port: int = 0):
#         return await self._loop.sock_sendall(self._socket, data)
#
#     async def close(self):
#         self._closed = True
#         self._socket.close()
