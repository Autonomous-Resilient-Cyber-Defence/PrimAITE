.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

Simulation State
================

``SimComponent`` objects in the simulation have a method called ``describe_state`` which return a dictionary of the state of the component. This is used to report pertinent data that could impact an agent's actions or rewards. For instance, the name and health status of a node is reported, which can be used by a reward function to punish corrupted or compromised nodes and reward healthy nodes. Each ``SimComponent`` object reports not only its own attributes in the state but also those of its child components. I.e. a computer node will report the state of its ``FileSystem`` and the ``FileSystem`` will report the state of its files and folders. This happens by recursively calling the children's own ``describe_state`` methods.

The game layer calls ``describe_state`` on the trunk ``SimComponent`` (the top-level parent) and then passes the state to the agents once per simulation step. For this reason, all ``SimComponent`` objects must have a ``describe_state`` method, and they must all be linked to the trunk ``SimComponent``.

This code snippet demonstrates how the state information is defined within the ``SimComponent`` class:

.. code-block:: python

    class Node(SimComponent, ABC):
        """
        A basic Node class that represents a node on the network.

        This class manages the state of the node, including the NICs (Network Interface Cards), accounts, applications,
        services, processes, file system, and various managers like ARP, ICMP, SessionManager, and SoftwareManager.

        :param hostname: The node hostname on the network.
        :param operating_state: The node operating state, either ON or OFF.
        """

        operating_state: NodeOperatingState = NodeOperatingState.OFF
        "The hardware state of the node."
        network_interfaces: Dict[str, NetworkInterface] = {}
        "The Network Interfaces on the node."
        network_interface: Dict[int, NetworkInterface] = {}
        "The Network Interfaces on the node by port id."
        accounts: Dict[str, Account] = {}
        "All accounts on the node."
        applications: Dict[str, Application] = {}
        "All applications on the node."
        services: Dict[str, Service] = {}
        "All services on the node."
        processes: Dict[str, Process] = {}
        "All processes on the node."
        file_system: FileSystem
        "The nodes file system."

    ...
    class ConfigSchema(BaseModel, ABC):
        """Configuration Schema for Node based classes."""

        ...
            revealed_to_red: bool = False
            "Informs whether the node has been revealed to a red agent."

    ...
    def describe_state(self) -> Dict:
    """
    Produce a dictionary describing the current state of this object.

    Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

    :return: Current state of this object and child objects.
    :rtype: Dict
    """
    state = super().describe_state()
    state.update(
        {
            "hostname": self.config.hostname,
            "operating_state": self.operating_state.value,
            "NICs": {
                eth_num: network_interface.describe_state()
                for eth_num, network_interface in self.network_interface.items()
            },
            "file_system": self.file_system.describe_state(),
            "applications": {app.name: app.describe_state() for app in self.applications.values()},
            "services": {svc.name: svc.describe_state() for svc in self.services.values()},
            "process": {proc.name: proc.describe_state() for proc in self.processes.values()},
            "revealed_to_red": self.config.revealed_to_red,
        }
    )
    return state
    ...
