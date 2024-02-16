.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


``simulation``
==============
In this section the network layout is defined. This part of the config follows a hierarchical structure. Almost every component defines a ``ref`` field which acts as a human-readable unique identifier, used by other parts of the config, such as agents.

At the top level of the network are ``nodes`` and ``links``.

**nodes:**
    * ``type``: one of ``router``, ``switch``, ``computer``, or ``server``, this affects what other sub-options should be defined.
    * ``hostname`` - a non-unique name used for logging and outputs.
    * ``num_ports`` (optional, routers and switches only): number of network interfaces present on the device.
    * ``ports`` (optional, routers and switches only): configuration for each network interface, including IP address and subnet mask.
    * ``acl`` (Router only): Define the ACL rules at each index of the ACL on the router. the possible options are: ``action`` (PERMIT or DENY), ``src_port``, ``dst_port``, ``protocol``, ``src_ip``, ``dst_ip``. Any options left blank default to none which usually means that it will apply across all options. For example leaving ``src_ip`` blank will apply the rule to all IP addresses.
    * ``services`` (computers and servers only): a list of services to install on the node. They must define a ``ref``, ``type``, and ``options`` that depend on which ``type`` was selected.
    * ``applications`` (computer and servers only): Similar to services. A list of application to install on the node.
    * ``network_interfaces`` (computers and servers only): If the node has multiple networking devices, the second, third, fourth, etc... must be defined here with an ``ip_address`` and ``subnet_mask``.

**links:**
    * ``ref``: unique identifier for this link
    * ``endpoint_a_ref``: Reference to the node at the first end of the link
    * ``endpoint_a_port``: The ethernet port or switch port index of the second node
    * ``endpoint_b_ref``: Reference to the node at the second end of the link
    * ``endpoint_b_port``: The ethernet port or switch port index on the second node
