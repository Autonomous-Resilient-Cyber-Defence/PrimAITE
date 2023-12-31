# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
"""A class that implements an access control list rule."""
from primaite.common.enums import RulePermissionType


class ACLRule:
    """Access Control List Rule class."""

    def __init__(
        self, _permission: RulePermissionType, _source_ip: str, _dest_ip: str, _protocol: str, _port: str
    ) -> None:
        """
        Initialise an ACL Rule.

        :param _permission: The permission (ALLOW or DENY)
        :param _source_ip: The source IP address
        :param _dest_ip: The destination IP address
        :param _protocol: The rule protocol
        :param _port: The rule port
        """
        self.permission: RulePermissionType = _permission
        self.source_ip: str = _source_ip
        self.dest_ip: str = _dest_ip
        self.protocol: str = _protocol
        self.port: str = _port

    def __hash__(self) -> int:
        """
        Override the hash function.

        Returns:
             Returns hash of core parameters.
        """
        return hash(
            (
                self.permission,
                self.source_ip,
                self.dest_ip,
                self.protocol,
                self.port,
            )
        )

    def get_permission(self) -> str:
        """
        Gets the permission attribute.

        Returns:
             Returns permission attribute
        """
        return self.permission

    def get_source_ip(self) -> str:
        """
        Gets the source IP address attribute.

        Returns:
             Returns source IP address attribute
        """
        return self.source_ip

    def get_dest_ip(self) -> str:
        """
        Gets the desintation IP address attribute.

        Returns:
             Returns destination IP address attribute
        """
        return self.dest_ip

    def get_protocol(self) -> str:
        """
        Gets the protocol attribute.

        Returns:
             Returns protocol attribute
        """
        return self.protocol

    def get_port(self) -> str:
        """
        Gets the port attribute.

        Returns:
             Returns port attribute
        """
        return self.port
