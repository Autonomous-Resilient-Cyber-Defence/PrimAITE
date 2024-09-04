.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

``ref``
=======

Human readable name used as reference for the |SOFTWARE_NAME_BACKTICK|. Not used in code.

``type``
========

The type of software that should be added. To add |SOFTWARE_NAME| this must be |SOFTWARE_NAME_BACKTICK|.

``options``
===========

The configuration options are the attributes that fall under the options for an application.



``fix_duration``
""""""""""""""""

Optional. Default value is ``2``.

The number of timesteps the |SOFTWARE_NAME| will remain in a ``FIXING`` state before going into a ``GOOD`` state.


``listen_on_ports``
"""""""""""""""""""

The set of ports to listen on. This is in addition to the main port the software is designated. This can either be
the string name of ports or the port integers

Example:

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: client
          type: computer
          ip_address: 192.168.10.11
          subnet_mask: 255.255.255.0
          default_gateway: 192.168.10.1
          services:
            - type: [Service Type]
              options:
                listen_on_ports:
                  - 631
          applications:
              - type: [Application Type]
                options:
                  listen_on_ports:
                    - SMB
