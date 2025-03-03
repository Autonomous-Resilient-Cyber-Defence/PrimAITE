.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _extensible_nodes:


Extensible Nodes
****************

Node classes within PrimAITE have been updated to allow for easier generation of custom nodes within simulations.


Changes to Node Class structure.
================================

Node classes all inherit from the base Node Class, though new classes should inherit from either HostNode or NetworkNode, subject to the intended application of the Node.

The use of an `__init__` method is not necessary, as configurable variables for the class should be specified within the `config` of the class, and passed at run time via your YAML configuration using the `from_config` method.

An example of how additional Node classes is below, taken from `router.py` within PrimAITE.

.. code-block:: Python

class Router(NetworkNode, identifier="router"):
    """ Represents a network router within the simulation, managing routing and forwarding of IP packets across network interfaces."""

    SYSTEM_SOFTWARE: ClassVar[Dict] = {
        "user-session-manager": UserSessionManager,
        "user-manager": UserManager,
        "terminal": Terminal,
    }

    network_interfaces: Dict[str, RouterInterface] = {}
    "The Router Interfaces on the node."
    network_interface: Dict[int, RouterInterface] = {}
    "The Router Interfaces on the node by port id."

    sys_log: SysLog

    config: "Router.ConfigSchema" = Field(default_factory=lambda: Router.ConfigSchema())

    class ConfigSchema(NetworkNode.ConfigSchema):
        """Configuration Schema for Router Objects."""

        num_ports: int = 5

        hostname: str = "Router"



Changes to YAML file.
=====================

While effort has been made to ensure that nodes defined within configuration YAML files for use with PrimAITE 3.X remain compatible with PrimAITE v4+, it is encouraged to review for minor changes needed.
