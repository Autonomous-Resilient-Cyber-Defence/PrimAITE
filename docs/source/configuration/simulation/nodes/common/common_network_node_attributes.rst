.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

``routes``
----------

A list of routes which tells the |NODE| where to forward the packet to depending on the target IP address.

e.g.

.. code-block:: yaml

    nodes:
        - ref: node
        ...
        routes:
            - address: 192.168.0.10
            subnet_mask: 255.255.255.0
            next_hop_ip_address: 192.168.1.1
            metric: 0

``address``
"""""""""""

The target IP address for the route. If the packet destination IP address matches this, the router will route the packet according to the ``next_hop_ip_address``.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``subnet_mask``
"""""""""""""""

Optional. Default value is ``255.255.255.0``.

The subnet mask setting for the route.

``next_hop_ip_address``
"""""""""""""""""""""""

The IP address of the next hop IP address that the packet will follow if the address matches the packet's destination IP address.

This must be a valid octet i.e. in the range of ``0.0.0.0`` and ``255.255.255.255``.

``metric``
""""""""""

Optional. Default value is ``0``. This value accepts floats.

The cost or distance of a route. The higher the value, the more cost or distance is attributed to the route.
