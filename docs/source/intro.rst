Intro
================

RakNet is a game engine solely managing networking and related services.
It includes game-level replication, patching, NAT punchthrough, and voice chat.
It allows any application to communicate with other applications that also uses it,
whether that be on the same computer, over a LAN, or over the internet.
Although RakNet can be used for any networked application,
it was developed with a focus on online gaming and provides extra functionality
to facilitate the programming of online games as well as being programmed to
address the most common needs of online games


About Networking
-----------------
Game network connections usually fall under two general categories:
- Peer to Peer Connectivity
- client/Server Connectivity.

Each of these are implemented in a variety of ways and with a variety of protocols.
However, RakNet supports any topology. It uses UDP-connectivity to send data across the network.

Reason for using UDP
---------------------
Generally speaking, the fastest computer with the best connection should act as the server, with other computers acting as the clients.

While there are many types of ways to encode packets, they are all transmitted as either UDP or TCP packets.
TCP packets are good for sending files, but not so good for games.
They are often delayed (resulting in games with a lot of lag) and arrive as streams rather than packets
(so you have to implement your own scheme to separate data). UDP packets are good because they are sent right away
and are sent in packets so you can easily distinguish data.

Associated Problems
--------------------
The added flexibility due to use of UDP comes with a variety of problems:
* UDP packets are not guaranteed to arrive. You may get all the packets you sent, none of them, or some fraction of them.
* UDP packets are not guaranteed to arrive in any order. This can be a huge problem when programming games. For example you may get the message that a tank was destroyed before you ever got the message that that tank had been created!
* UDP packets are guaranteed to arrive with correct data, but have no protection from hackers intercepting and changing the data once it has arrived.
* UDP packets do not require a connection to be accepted. This sounds like a good thing until you realize that games without protection from this would be very easy to hack. For example, if you had a message that said "Give such and such invulnerability" a hacker could copy that message and send it to the server everytime they wanted invulnerability.
* The UDP transport does not provide flow control or aggregation so it is possible to overrun the recipient and to send data inefficiently.

How RakNet helps with these issues?
-----------------------------------
At the lowest level, RakNet's peer to peer class, RakPeerInterface provides a layer over UDP packets that handle these problems transparently, allowing the programmer to focus on the game rather than worrying about the engine.
* RakNet can automatically resend packets that did not arrive.
* RakNet can automatically order or sequence packets that arrived out of order, and does so efficiently.
* RakNet protects data that is transmitted, and will inform the programmer if that data was externally changed.
* RakNet provides a fast, simple, connection layer that blocks unauthorized transmission.
* RakNet transparently handles network issues such as flow control and aggreggation.

Why use RakNet over other netowrk APIs?
---------------------------------------
Unlike some other networking APIs:
- RakNet adds very few bytes to your data.
- RakNet does not incur overhead for features you do not use.
- RakNet has nearly instantaneous connections and disconnections.
- RakNet does not assume the internet is reliable. RakNet will gracefully handle connection problems rather than block, lock-up, or crash.
- RakNet technology has been successfully used in dozens of games. It's been proven to work.
- RakNet is easy to use and understand.

What is Aio-Rak-Net?
---------------------
Aio-Rak-Net is a library that provides a high level interface to RakNet, implemented in python, providing a :ref:`server-interface <server>` for RakNet.