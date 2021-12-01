Packets
================

.. currentmodule:: rak_net.protocol

Following Packet implementations are used in this module:

Protocol Packets
----------------

.. autoclass:: Packet
    :members:
    :member-order: bysource
    :noindex:

.. autoclass:: Acknowledgement
    :members:
    :member-order: bysource

.. autoclass:: Ack
    :members:
    :member-order:

.. autoclass:: Nack
    :members:
    :member-order: bysource

.. autoclass:: ConnectionRequest
    :members:
    :member-order: bysource

.. autoclass:: ConnectionRequestAccepted
    :members:
    :member-order: bysource

.. autoclass:: Disconnect
    :members:
    :member-order: bysource

.. autoclass:: NewIncomingConnection
    :members:
    :member-order: bysource

.. autoclass:: IncompatibleProtocolVersion
    :members:
    :member-order: bysource

.. autoclass:: OpenConnectionRequest1
    :members:
    :member-order: bysource

.. autoclass:: OpenConnectionReply1
    :members:
    :member-order: bysource

.. autoclass:: OpenConnectionRequest2
    :members:
    :member-order: bysource

.. autoclass:: OpenConnectionReply2
    :members:
    :member-order: bysource

.. autoclass:: OnlinePing
    :members:
    :member-order: bysource

.. autoclass:: OnlinePong
    :members:
    :member-order: bysource

.. autoclass:: OfflinePing
    :members:
    :member-order: bysource

.. autoclass:: OfflinePong
    :members:
    :member-order: bysource


Frames
-------
Almost all of the relavant data is contained in the payload of the packet.
The payload is stored in the form of a set of bytes, termed as a frame.

.. autoclass:: rak_net.frame.Frame
    :members:
    :member-order: bysource

.. autoclass:: FrameSet
    :members:
    :member-order: bysource

