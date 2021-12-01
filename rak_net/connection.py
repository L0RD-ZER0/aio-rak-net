from __future__ import annotations
from typing import TYPE_CHECKING
from asyncio import Lock as _Lock, iscoroutine, iscoroutinefunction
from .protocol.packet import protocol_packets
from .protocol import ProtocolInfo
from .frame import Frame
from time import time
from .utils import ReliabilityTool
if TYPE_CHECKING:
    from .utils import InternetAddress
    from .server import Server


class Connection:
    """
    Class representing a connection

    :param address: Address of the connection
    :param mtu_size: MTU-Size of the connection
    :param server: Server using which the connection is made
    :param timeout: Timeout period of the connection
    :param lock: Lock for the connection. Will be created if not supplied
    """

    __slots__ = ('address', 'mtu_size', 'server', 'connected', 'recovery_queue', 'ack_queue', 'nack_queue',
                 'fragmented_packets', 'compound_id', 'receive_sequence_numbers', 'send_sequence_number',
                 'receive_sequence_number', 'send_reliable_frame_index', 'receive_reliable_frame_index',
                 'queue', 'send_order_channel_index', 'send_sequence_channel_index', 'last_receive_time',
                 'ms', 'last_ping_time', '_timeout', '_lock', 'interface')

    def __init__(self, address: InternetAddress, mtu_size: int, server: Server, *, timeout: int = 10, lock: _Lock = None):
        self.address: InternetAddress = address
        self.mtu_size: int = mtu_size
        self.server: Server = server
        self.connected: bool = False
        self.recovery_queue: dict[int, protocol_packets.FrameSet] = {}
        self.ack_queue: list[int] = []
        self.nack_queue: list[int] = []
        self.fragmented_packets: dict[int, (int, Frame)] = {}
        self.compound_id: int = 0
        self.receive_sequence_numbers: list[int] = []
        self.send_sequence_number: int = 0
        self.receive_sequence_number: int = 0
        self.send_reliable_frame_index: int = 0
        self.receive_reliable_frame_index: int = 0
        self.queue: protocol_packets.FrameSet = protocol_packets.FrameSet()
        self.send_order_channel_index: list[int] = [0] * 32
        self.send_sequence_channel_index: list[int] = [0] * 32
        self.last_receive_time: float = time()
        self.ms: int = 0
        self.last_ping_time: float = time()
        self._timeout = timeout
        self._lock = lock or _Lock()

    async def update(self) -> None:
        """
        Method to update the connection
        """
        if (time() - self.last_receive_time) >= self._timeout:
            await self.disconnect()
        if self.connected:
            if (time() - self.last_ping_time) >= 1:
                self.last_ping_time = time()
                await self.ping()
        await self.send_ack_queue()
        await self.send_nack_queue()
        await self.send_queue()

    async def ping(self) -> None:
        """
        Method for a ping
        """
        packet: protocol_packets.OnlinePing = protocol_packets.OnlinePing()
        packet.client_timestamp = self.server.get_time_ms()
        packet.encode()
        new_frame: Frame = Frame()
        new_frame.reliability = 0
        new_frame.body = packet.data
        await self.add_to_queue(new_frame)

    async def send_data(self, data: bytes, *, address: InternetAddress = None) -> None:
        """
        Send data to the given address

        :param data: Data to be sent
        :param address: Address to which the data is to be sent
        """
        address = address or self.address
        return await self.server.send_data(data, address)

    async def handle(self, data: bytes) -> None:
        """
        Function to handle the incoming connection data

        :param data: Incoming data to be handled
        """
        self.last_receive_time = time()
        if data[0] == ProtocolInfo.ACK:
            await self.handle_ack(data)
        elif data[0] == ProtocolInfo.NACK:
            await self.handle_nack(data)
        elif (data[0] & ProtocolInfo.FRAME_SET) != 0:
            await self.handle_frame_set(data)

    async def handle_ack(self, data: bytes) -> None:
        """
        Handler for `ACK`

        :param data: Data to be handled
        """
        packet: protocol_packets.Ack = protocol_packets.Ack(data)
        packet.decode()
        for sequence_number in packet.sequence_numbers:
            if sequence_number in self.recovery_queue:
                async with self._lock:
                    del self.recovery_queue[sequence_number]

    async def handle_nack(self, data: bytes) -> None:
        """
        Handler for `NACK`

        :param data: Data to be handled
        """
        packet: protocol_packets.Nack = protocol_packets.Nack(data)
        packet.decode()
        for sequence_number in packet.sequence_numbers:
            if sequence_number in self.recovery_queue:
                async with self._lock:
                    lost_packet: protocol_packets.FrameSet = self.recovery_queue[sequence_number]
                lost_packet.sequence_number = self.send_sequence_number
                self.send_sequence_number += 1
                lost_packet.encode()
                await self.send_data(lost_packet.data)
                async with self._lock:
                    del self.recovery_queue[sequence_number]

    async def handle_frame_set(self, data: bytes) -> None:
        """
        Handler for a frame set

        :param data: Data to be handled
        """
        packet: protocol_packets.FrameSet = protocol_packets.FrameSet(data)
        packet.decode()
        if packet.sequence_number not in self.receive_sequence_numbers:
            async with self._lock:
                if packet.sequence_number in self.nack_queue:
                    self.nack_queue.remove(packet.sequence_number)
                self.receive_sequence_numbers.append(packet.sequence_number)
                self.ack_queue.append(packet.sequence_number)
            hole_size: int = packet.sequence_number - self.receive_sequence_number
            if hole_size > 0:
                for sequence_number in range(self.receive_sequence_number + 1, hole_size):
                    if sequence_number not in self.receive_sequence_numbers:
                        async with self._lock:
                            self.nack_queue.append(sequence_number)
            self.receive_sequence_number = packet.sequence_number
            for frame in packet.frames:
                if not ReliabilityTool.reliable(frame.reliability):
                    await self.handle_frame(frame)
                else:
                    hole_size: int = frame.reliable_frame_index - self.receive_reliable_frame_index
                    if hole_size == 0:
                        await self.handle_frame(frame)
                        self.receive_reliable_frame_index += 1

    async def handle_fragmented_frame(self, frame: Frame) -> None:
        """
        Handler for a fragmented frame

        :param frame: Frame to be handled
        """
        if frame.compound_id not in self.fragmented_packets:
            self.fragmented_packets[frame.compound_id] = {frame.index: frame}
        else:
            self.fragmented_packets[frame.compound_id][frame.index] = frame
        if len(self.fragmented_packets[frame.compound_id]) == frame.compound_size:
            new_frame: Frame = Frame()
            new_frame.body = b""
            for i in range(0, frame.compound_size):
                new_frame.body += self.fragmented_packets[frame.compound_id][i].body
            del self.fragmented_packets[frame.compound_id]
            await self.handle_frame(new_frame)

    async def handle_frame(self, frame: Frame) -> None:
        """
        Handler for a frame

        :param frame: Frame to be handled
        """
        if frame.fragmented:
            await self.handle_fragmented_frame(frame)
        else:
            if not self.connected:
                if frame.body[0] == ProtocolInfo.CONNECTION_REQUEST:
                    new_frame: Frame = Frame()
                    new_frame.reliability = 0
                    new_frame.body = await self.server.handler.handle_connection_request(frame.body, self.address, self.server)
                    await self.add_to_queue(new_frame)
                elif frame.body[0] == ProtocolInfo.CONNECTION_REQUEST_ACCEPTED:
                    new_frame: Frame = Frame()
                    new_frame.reliability = 0
                    new_frame.body = await self.server.handler.handle_connection_request_accepted(frame.body, self.address, self.server)
                    await self.add_to_queue(new_frame)
                    self.connected = True
                elif frame.body[0] == ProtocolInfo.NEW_INCOMING_CONNECTION:
                    packet: protocol_packets.NewIncomingConnection = protocol_packets.NewIncomingConnection(frame.body)
                    packet.decode()
                    if packet.server_address.port == self.server.address.port:
                        self.connected = True
                        if hasattr(self.server, "interface"):
                            if hasattr(self.server.interface, "on_new_incoming_connection"):
                                if iscoroutine(self.server.interface.on_new_incoming_connection):
                                    await self.server.interface.on_new_incoming_connection
                                elif iscoroutinefunction(self.server.interface.on_new_incoming_connection):
                                    await self.server.interface.on_new_incoming_connection(self)
                                else:
                                    self.server.interface.on_new_incoming_connection(self)
            elif frame.body[0] == ProtocolInfo.ONLINE_PING:
                new_frame: Frame = Frame()
                new_frame.reliability = 0
                new_frame.body = await self.server.handler.handle_online_ping(frame.body, self.address, self.server)
                await self.add_to_queue(new_frame)
            elif frame.body[0] == ProtocolInfo.ONLINE_PONG:
                packet: protocol_packets.OnlinePong = protocol_packets.OnlinePong(frame.body)
                packet.decode()
                self.ms = (self.server.get_time_ms() - packet.client_timestamp)
            elif frame.body[0] == ProtocolInfo.DISCONNECT:
                await self.disconnect()
            else:
                if hasattr(self.server, "interface"):
                    if hasattr(self.server.interface, "on_frame"):
                        if iscoroutine(self.server.interface.on_frame):
                            await self.server.interface.on_frame
                        elif iscoroutinefunction(self.server.interface.on_frame):
                            await self.server.interface.on_frame(self)
                        else:
                            self.server.interface.on_frame(self)

    async def send_queue(self) -> None:
        """
        Method to send the queue
        """
        if len(self.queue.frames) > 0:
            self.queue.sequence_number = self.send_sequence_number
            self.send_sequence_number += 1
            self.recovery_queue[self.queue.sequence_number] = self.queue
            self.queue.encode()
            await self.send_data(self.queue.data)
            self.queue = protocol_packets.FrameSet()

    async def append_frame(self, frame: Frame, immediate: bool = False) -> None:
        """
        Method to append a frame to the queue

        :param frame: Frame to be appended
        :param immediate: Adds to the front of queue if True, defaults to False and adds to back of the queue
        """
        if immediate:
            packet: protocol_packets.FrameSet = protocol_packets.FrameSet()
            packet.frames.append(frame)
            packet.sequence_number = self.send_sequence_number
            self.send_sequence_number += 1
            async with self._lock:
                self.recovery_queue[packet.sequence_number] = packet
            packet.encode()
            await self.send_data(packet.data)
        else:
            frame_size: int = frame.size
            queue_size: int = self.queue.size
            if frame_size + queue_size >= self.mtu_size:
                await self.send_queue()
            self.queue.frames.append(frame)

    async def add_to_queue(self, frame: Frame) -> None:
        """
        Method to process and add a frame to the queue
        :param frame: Frame to be added
        """
        if ReliabilityTool.ordered(frame.reliability):
            frame.ordered_frame_index = self.send_order_channel_index[frame.order_channel]
            self.send_order_channel_index[frame.order_channel] += 1
        elif ReliabilityTool.sequenced(frame.reliability):
            frame.ordered_frame_index = self.send_order_channel_index[frame.order_channel]
            frame.sequenced_frame_index = self.send_sequence_channel_index[frame.order_channel]
            self.send_sequence_channel_index[frame.order_channel] += 1
        if frame.size > self.mtu_size:
            fragmented_body: list[bytes] = []
            for i in range(0, len(frame.body), self.mtu_size):
                fragmented_body.append(frame.body[i:i + self.mtu_size])
            for index, body in enumerate(fragmented_body):
                new_frame: Frame = Frame()
                new_frame.fragmented = True
                new_frame.reliability = frame.reliability
                new_frame.compound_id = self.compound_id
                new_frame.compound_size = len(fragmented_body)
                new_frame.index = index
                new_frame.body = body
                if ReliabilityTool.reliable(frame.reliability):
                    new_frame.reliable_frame_index = self.send_reliable_frame_index
                    self.send_reliable_frame_index += 1
                if ReliabilityTool.sequenced_or_ordered(frame.reliability):
                    new_frame.ordered_frame_index = frame.ordered_frame_index
                    new_frame.order_channel = frame.order_channel
                if ReliabilityTool.sequenced(frame.reliability):
                    new_frame.sequenced_frame_index = frame.sequenced_frame_index
                await self.append_frame(new_frame, True)
            self.compound_id += 1
        else:
            if ReliabilityTool.reliable(frame.reliability):
                frame.reliable_frame_index = self.send_reliable_frame_index
                self.send_reliable_frame_index += 1
            await self.append_frame(frame, False)

    async def send_ack_queue(self) -> None:
        """
        Method to send data in the ACK-Queue
        """
        if len(self.ack_queue) > 0:
            packet: protocol_packets.Ack = protocol_packets.Ack()
            packet.sequence_numbers = self.ack_queue.copy()
            packet.encode()
            self.ack_queue.clear()
            await self.send_data(packet.data)

    async def send_nack_queue(self) -> None:
        """
        Method to send data in the NACK-Queue
        """
        if len(self.nack_queue) > 0:
            packet: protocol_packets.Nack = protocol_packets.Nack()
            packet.sequence_numbers = self.nack_queue.copy()
            packet.encode()
            self.nack_queue.clear()
            await self.send_data(packet.data)

    async def disconnect(self) -> None:
        """
        Method to disconnect the connection
        """
        new_frame: Frame = Frame()
        new_frame.reliability = 0
        new_frame.body = b"\x15"
        await self.add_to_queue(new_frame)
        await self.server.remove_connection(self.address)
        if hasattr(self.server, "interface"):
            if hasattr(self.server.interface, "on_disconnect"):
                if iscoroutine(self.server.interface.on_disconnect):
                    await self.server.interface.on_disconnect
                elif iscoroutinefunction(self.server.interface.on_disconnect):
                    await self.server.interface.on_disconnect(self)
                else:
                    self.server.interface.on_disconnect(self)

    def __repr__(self):
        return f'<Connection: {self.address.token}>'
