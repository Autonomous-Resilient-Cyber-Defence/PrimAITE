"""User account simulation."""
from enum import Enum
from typing import Dict

from primaite import getLogger
from primaite.simulator.core import SimComponent

_LOGGER = getLogger(__name__)


class AccountType(Enum):
    """Whether the account is intended for a user to log in or for a service to use."""

    SERVICE = 1
    "Service accounts are used to grant permissions to software on nodes to perform actions"
    USER = 2
    "User accounts are used to allow agents to log in and perform actions"


class PasswordPolicyLevel(Enum):
    """Complexity requirements for account passwords."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


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
    enabled: bool = True

    def describe_state(self) -> Dict:
        """Describe state for agent observations."""
        return super().describe_state()

    def enable(self):
        """Set the status to enabled."""
        self.enabled = True

    def disable(self):
        """Set the status to disabled."""
        self.enabled = False

    def log_on(self) -> None:
        """TODO."""
        self.num_logons += 1

    def log_off(self) -> None:
        """TODO."""
        self.num_logoffs += 1
