.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

``ip_address``
--------------

The IP address of the |NODE| in the network.

``subnet_mask``
---------------

Optional. Default value is ``255.255.255.0``.

The subnet mask for the |NODE| to use.

``default_gateway``
-------------------

The IP address that the |NODE| will use as the default gateway. Typically, this is the IP address of the closest router that the |NODE| is connected to.

``dns_server``
--------------

Optional. Default value is ``None``

The IP address of the node which holds an instance of the :ref:`DNSServer`. Some applications may use a domain name e.g. the :ref:`WebBrowser`

.. include:: ../software/applications.rst

.. include:: ../software/services.rst
