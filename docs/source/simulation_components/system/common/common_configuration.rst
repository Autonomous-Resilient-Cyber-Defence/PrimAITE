.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

.. _Common Configuration:

Common Configuration
""""""""""""""""""""

ref
"""

Human readable name used as reference for the software class. Not used in code.

type
""""

The type of software that should be added. To add the required software, this must be it's name.

options
"""""""

The configuration options are the attributes that fall under the options for an application or service.

fix_duration
""""""""""""

Optional. Default value is ``2``.

The number of timesteps the software will remain in a ``FIXING`` state before going into a ``GOOD`` state.


listen_on_ports
^^^^^^^^^^^^^^^

Optional. The set of ports to listen on. This is in addition to the main port the software is designated. This can either be
the string name of ports or the port integers

Example:

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: [hostname]
          type: [Node Type]
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
