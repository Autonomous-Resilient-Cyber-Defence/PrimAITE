# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""The link class."""
from typing import List

from primaite.common.protocol import Protocol


class Link(object):
    """Link class."""

    def __init__(self, _id, _bandwidth, _source_node_name, _dest_node_name, _services):
        """
        Init.

        Args:
            _id: The IER id
            _bandwidth: The bandwidth of the link (bps)
            _source_node_name: The name of the source node
            _dest_node_name: The name of the destination node
            _protocols: The protocols to add to the link
        """
        self.id = _id
        self.bandwidth = _bandwidth
        self.source_node_name = _source_node_name
        self.dest_node_name = _dest_node_name
        self.protocol_list: List[Protocol] = []

        # Add the default protocols
        for protocol_name in _services:
            self.add_protocol(protocol_name)

    def add_protocol(self, _protocol):
        """
        Adds a new protocol to the list of protocols on this link.

        Args:
            _protocol: The protocol to be added (enum)
        """
        self.protocol_list.append(Protocol(_protocol))

    def get_id(self):
        """
        Gets link ID.

        Returns:
             Link ID
        """
        return self.id

    def get_source_node_name(self):
        """
        Gets source node name.

        Returns:
             Source node name
        """
        return self.source_node_name

    def get_dest_node_name(self):
        """
        Gets destination node name.

        Returns:
             Destination node name
        """
        return self.dest_node_name

    def get_bandwidth(self):
        """
        Gets bandwidth of link.

        Returns:
             Link bandwidth (bps)
        """
        return self.bandwidth

    def get_protocol_list(self):
        """
        Gets list of protocols on this link.

        Returns:
             List of protocols on this link
        """
        return self.protocol_list

    def get_current_load(self):
        """
        Gets current total load on this link.

        Returns:
             Total load on this link (bps)
        """
        total_load = 0
        for protocol in self.protocol_list:
            total_load += protocol.get_load()
        return total_load

    def add_protocol_load(self, _protocol, _load):
        """
        Adds a loading to a protocol on this link.

        Args:
            _protocol: The protocol to load
            _load: The amount to load (bps)
        """
        for protocol in self.protocol_list:
            if protocol.get_name() == _protocol:
                protocol.add_load(_load)
            else:
                pass

    def clear_traffic(self):
        """Clears all traffic on this link."""
        for protocol in self.protocol_list:
            protocol.clear_load()
