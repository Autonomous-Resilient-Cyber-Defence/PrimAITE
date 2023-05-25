# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""A class that implements an access control list rule."""


class ACLRule:
    """Access Control List Rule class."""

    def __init__(self, _permission, _source_ip, _dest_ip, _protocol, _port):
        """
        Init.

        Args:
            _permission: The permission (ALLOW or DENY)
            _source_ip: The source IP address
            _dest_ip: The destination IP address
            _protocol: The rule protocol
            _port: The rule port
        """
        self.permission = _permission
        self.source_ip = _source_ip
        self.dest_ip = _dest_ip
        self.protocol = _protocol
        self.port = _port

    def __hash__(self):
        """
        Override the hash function.

        Returns:
             Returns hash of core parameters.
        """
        return hash(
            (self.permission, self.source_ip, self.dest_ip, self.protocol, self.port)
        )

    def get_permission(self):
        """
        Gets the permission attribute.

        Returns:
             Returns permission attribute
        """
        return self.permission

    def get_source_ip(self):
        """
        Gets the source IP address attribute.

        Returns:
             Returns source IP address attribute
        """
        return self.source_ip

    def get_dest_ip(self):
        """
        Gets the desintation IP address attribute.

        Returns:
             Returns destination IP address attribute
        """
        return self.dest_ip

    def get_protocol(self):
        """
        Gets the protocol attribute.

        Returns:
             Returns protocol attribute
        """
        return self.protocol

    def get_port(self):
        """
        Gets the port attribute.

        Returns:
             Returns port attribute
        """
        return self.port
