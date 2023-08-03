"""User account simulation."""
from enum import Enum
from typing import Callable, Dict, List, TypeAlias

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


class PasswordPolicyLevel(Enum):
    """Complexity requirements for account passwords."""

    low = 1
    medium = 2
    high = 3


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
    status: AccountStatus = AccountStatus.disabled

    def enable(self):
        """Set the status to enabled."""
        self.status = AccountStatus.enabled

    def disable(self):
        """Set the status to disabled."""
        self.status = AccountStatus.disabled

    def _possible_actions(self) -> Dict[str, Callable[[List[str]], None]]:
        return {
            "enable": self.enable,
            "disable": self.disable,
        }
