.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _network_node_adder:

Network Node Adder Module
#########################

This module provides a framework for adding nodes to a network in a standardised way. It defines a base class ``NetworkNodeAdder``, which can be extended to create specific node adders, and utility functions to calculate network infrastructure requirements.

The module allows you to use the pre-defined node adders, ``OfficeLANAdder``, or create custom ones by extending the base class.

How It Works
============

The main class in the module is ``NetworkNodeAdder``, which defines the interface for adding nodes to a network. Child classes are expected to:

1. Define a ``ConfigSchema`` nested class to define configuration options.
2. Implement the ``add_nodes_to_net(config, network)`` method, which adds the nodes to the network according to the configuration object.

The ``NetworkNodeAdder`` base class handles node adders defined in the primAITE config YAML file as well. It does this by keeping a registry of node adder classes, and uses the ``type`` field of the config to select the appropriate class to which to pass the configuration.

Example Usage
=============

Via Python API
--------------

Adding nodes to a network can be done using the python API by constructing the relevant ``ConfigSchema`` object like this:

.. code-block:: python

    net = Network()

    office_lan_config = OfficeLANAdder.ConfigSchema(
        lan_name="CORP-LAN",
        subnet_base=2,
        pcs_ip_block_start=10,
        num_pcs=8,
        include_router=False,
        bandwidth=150,
    )
    OfficeLANAdder.add_nodes_to_net(config=office_lan_config, network=net)

In this example, a network with 8 computers connected by a switch will be added to the network object.


Via YAML Config
---------------

.. code-block:: yaml
    simulation:
      network:
        nodes:
          # ... nodes go here
        node_sets:
          - type: office-lan
            lan_name: CORP_LAN
            subnet_base: 2
            pcs_ip_block_start: 10
            num_pcs: 8
            include_router: False
            bandwidth: 150
          # ... additional node sets can be added below

``NetworkNodeAdder`` reads the ``type`` property of the config, then constructs and passes the configuration to ``OfficeLANAdder.add_nodes_to_net()``.

In this example, a network with 8 computers connected by a switch will be added to the network object. Equivalent to the above.


Creating Custom Node Adders
===========================
To create a custom node adder, subclass NetworkNodeAdder and define:

* A ConfigSchema class that defines the configuration schema for the node adder.
* The add_nodes_to_net method that implements how nodes should be added to the network.

Example: DataCenterAdder
------------------------
Here is an example of creating a custom node adder, DataCenterAdder:

.. code-block:: python

    class DataCenterAdder(NetworkNodeAdder, discriminator="data-center"):
        class ConfigSchema(NetworkNodeAdder.ConfigSchema):
            type: Literal["data-center"] = "data-center"
            num_servers: int
            data_center_name: str

        @classmethod
        def add_nodes_to_net(cls, config: ConfigSchema, network: Network) -> None:
            for i in range(config.num_servers):
                server = Computer(
                    hostname=f"server_{i}_{config.data_center_name}",
                    ip_address=f"192.168.100.{i + 8}",
                    subnet_mask="255.255.255.0",
                    default_gateway="192.168.100.1",
                    start_up_duration=0
                )
                server.power_on()
                network.add_node(server)

**Using the Custom Node Adder:**

.. code-block:: python

    config = {
        "type": "data-center",
        "num_servers": 5,
        "data_center_name": "dc1"
    }

    network = Network()
    DataCenterAdder.from_config(config, network)
