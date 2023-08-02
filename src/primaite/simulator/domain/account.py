"""User account simulation."""
from enum import Enum
from typing import Dict, List, Set, TypeAlias

from primaite import getLogger
from primaite.simulator.core import SimComponent

_LOGGER = getLogger(__name__)


__temp_node = TypeAlias()  # placeholder while nodes don't exist


class AccountType(Enum):
    """Whether the account is intended for a user to log in or for a service to use."""

    service = 1
    "Service accounts are used to grant permissions to software on nodes to perform actions"
    user = 2
    "User accounts are used to allow agents to log in and perform actions"


class AccountGroup(Enum):
    """Permissions are set at group-level and accounts can belong to these groups."""

    local_user = 1
    "For performing basic actions on a node"
    domain_user = 2
    "For performing basic actions to the domain"
    local_admin = 3
    "For full access to actions on a node"
    domain_admin = 4
    "For full access"


class AccountStatus(Enum):
    """Whether the account is active."""

    enabled = 1
    disabled = 2


class Account(SimComponent):
    """User accounts."""

    num_logons: int = 0
    "The number of times this account was logged into since last reset."
    num_logoffs: int = 0
    "The number of times this account was logged out of since last reset."
    num_group_changes: int = 0
    "The number of times this account was moved in or out of an AccountGroup."
    username: str
    "Account username."
    password: str
    "Account password."
    account_type: AccountType
    "Account Type, currently this can be service account (used by apps) or user account."
    domain_groups: Set[AccountGroup] = []
    "Domain-wide groups that this account belongs to."
    local_groups: Dict[__temp_node, List[AccountGroup]]
    "For each node, whether this account has local/admin privileges on that node."
    status: AccountStatus = AccountStatus.disabled

    def add_to_domain_group(self, group: AccountGroup) -> None:
        """
        Add this account to a domain group.

        If the account is already a member of this group, nothing happens.

        :param group: The group to which to add this account.
        :type group: AccountGroup
        """
        self.domain_groups.add(group)

    def remove_from_domain_group(self, group: AccountGroup) -> None:
        """
        Remove this account from a domain group.

        If the account is already not a member of that group, nothing happens.

        :param group: The group from which this account should be removed.
        :type group: AccountGroup
        """
        self.domain_groups.discard(group)

    def enable_account(self):
        """Set the status to enabled."""
        self.status = AccountStatus.enabled

    def disable_account(self):
        """Set the status to disabled."""
        self.status = AccountStatus.disabled
