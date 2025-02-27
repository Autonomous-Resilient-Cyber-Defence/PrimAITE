.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _common_node_attributes:

``ref``
-------

Human readable name used as reference for the |NODE|. Not used in code.

``hostname``
------------

The hostname of the |NODE|. This will be used to reference the |NODE|.

``operating_state``
-------------------

The initial operating state of the node.

Optional. Default value is ``ON``.

Options available are:

- ``ON``
- ``OFF``
- ``BOOTING``
- ``SHUTTING_DOWN``

Note that YAML may assume non quoted ``ON`` and ``OFF`` as ``True`` and ``False`` respectively. To prevent this, use ``"ON"`` or ``"OFF"``

See :py:mod:`primaite.simulator.network.hardware.node_operating_state.NodeOperatingState`


``dns_server``
--------------

Optional. Default value is ``None``.

The IP address of the node which holds an instance of the :ref:`DNSServer`. Some applications may use a domain name e.g. the :ref:`WebBrowser`

``start_up_duration``
---------------------

Optional. Default value is ``3``.

The number of time steps required to occur in order for the node to cycle from ``OFF`` to ``BOOTING_UP`` and then finally ``ON``.

``shut_down_duration``
----------------------

Optional. Default value is ``3``.

The number of time steps required to occur in order for the node to cycle from ``ON`` to ``SHUTTING_DOWN`` and then finally ``OFF``.

``file_system``
---------------

Optional.

The file system of the node. This configuration allows nodes to be initialised with files and/or folders.

The file system takes a list of folders and files.

Example:

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: client_1
          type: computer
          ip_address: 192.168.10.11
          subnet_mask: 255.255.255.0
          default_gateway: 192.168.10.1
          file_system:
            - empty_folder  # example of an empty folder
            - downloads:
              - "test_1.txt"  # files in the downloads folder
              - "test_2.txt"
            - root:
              - passwords:  # example of file with size and type
                  size: 69  # size in bytes
                  type: TXT  # See FileType for list of available file types

List of file types: :py:mod:`primaite.simulator.file_system.file_type.FileType`

``users``
---------

The list of pre-existing users that are additional to the default admin user (``username=admin``, ``password=admin``).
Additional users are configured as an array and must contain a ``username``, ``password``, and can contain an optional
boolean ``is_admin``.

Example of adding two additional users to a node:

.. code-block:: yaml

    simulation:
      network:
        nodes:
        - hostname: [hostname]
          type: [Node Type]
          users:
            - username: jane.doe
              password: '1234'
              is_admin: true
            - username: john.doe
              password: password_1
              is_admin: false
