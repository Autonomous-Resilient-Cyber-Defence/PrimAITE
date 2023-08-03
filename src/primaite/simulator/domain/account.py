"""User account simulation."""
from enum import Enum
from typing import Any, Callable, Dict, List

from primaite import getLogger
from primaite.simulator.core import SimComponent

_LOGGER = getLogger(__name__)


class AccountType(Enum):
    """Whether the account is intended for a user to log in or for a service to use."""

    service = 1
    "Service accounts are used to grant permissions to software on nodes to perform actions"
    user = 2
    "User accounts are used to allow agents to log in and perform actions"


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
