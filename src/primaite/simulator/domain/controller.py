from enum import Enum
from typing import Any, Dict, Final, List

from primaite.simulator.core import ActionPermissionValidator, SimComponent
from primaite.simulator.domain.account import Account, AccountType


# placeholder while these objects don't yet exist
class temp_node:
    pass


class temp_application:
    pass


class temp_folder:
    pass


class temp_file:
    pass


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


class GroupMembershipValidator(ActionPermissionValidator):
    """Permit actions based on group membership."""

    def __init__(self, allowed_groups: List[AccountGroup]) -> None:
        """TODO."""
        self.allowed_groups = allowed_groups

    def __call__(self, request: List[str], context: Dict) -> bool:
        """Permit the action if the request comes from an account which belongs to the right group."""
        # if context request source is part of any groups mentioned in self.allow_groups, return true, otherwise false
        requestor_groups: List[str] = context["request_source"]["groups"]
        for allowed_group in self.allowed_groups:
            if allowed_group.name in requestor_groups:
                return True
        return False


class DomainController(SimComponent):
    """Main object for controlling the domain."""

    # owned objects
    accounts: List[Account] = []
    groups: Final[List[AccountGroup]] = list(AccountGroup)

    group_membership: Dict[AccountGroup, List[Account]]

    # references to non-owned objects
    nodes: List[temp_node] = []
    applications: List[temp_application] = []
    folders: List[temp_folder] = []
    files: List[temp_file] = []

    def _register_account(self, account: Account) -> None:
        """TODO."""
        ...

    def _deregister_account(self, account: Account) -> None:
        """TODO."""
        ...

    def create_account(self, username: str, password: str, account_type: AccountType) -> Account:
        """TODO."""
        ...

    def rotate_all_credentials(self) -> None:
        """TODO."""
        ...

    def rotate_account_credentials(self, account: Account) -> None:
        """TODO."""
        ...

    def add_account_to_group(self, account: Account, group: AccountGroup) -> None:
        """TODO."""
        ...

    def remove_account_from_group(self, account: Account, group: AccountGroup) -> None:
        """TODO."""
        ...
