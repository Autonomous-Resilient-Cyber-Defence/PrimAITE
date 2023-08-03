from typing import Dict, Final, List, TypeAlias

from primaite.simulator.core import SimComponent
from primaite.simulator.domain import Account, AccountGroup, AccountType

# placeholder while these objects don't yet exist
__temp_node = TypeAlias()
__temp_application = TypeAlias()
__temp_folder = TypeAlias()
__temp_file = TypeAlias()


class DomainController(SimComponent):
    """Main object for controlling the domain."""

    # owned objects
    accounts: List(Account) = []
    groups: Final[List[AccountGroup]] = list(AccountGroup)

    group_membership: Dict[AccountGroup, List[Account]]

    # references to non-owned objects
    nodes: List(__temp_node) = []
    applications: List(__temp_application) = []
    folders: List(__temp_folder) = []
    files: List(__temp_file) = []

    def register_account(self, account: Account) -> None:
        """TODO."""
        ...

    def deregister_account(self, account: Account) -> None:
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
