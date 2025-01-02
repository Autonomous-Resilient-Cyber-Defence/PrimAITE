# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from enum import Enum
from typing import Dict, Final, List, Literal, Tuple

from primaite.simulator.core import RequestManager, RequestPermissionValidator, RequestType, SimComponent
from primaite.simulator.domain.account import Account, AccountType


# placeholder while these objects don't yet exist
class temp_node:
    """Placeholder for node class for type hinting purposes."""

    pass


class temp_application:
    """Placeholder for application class for type hinting purposes."""

    pass


class temp_folder:
    """Placeholder for folder class for type hinting purposes."""

    pass


class temp_file:
    """Placeholder for file class for type hinting purposes."""

    pass


class AccountGroup(Enum):
    """Permissions are set at group-level and accounts can belong to these groups."""

    LOCAL_USER = 1
    "For performing basic actions on a node"
    DOMAIN_USER = 2
    "For performing basic actions to the domain"
    LOCAL_ADMIN = 3
    "For full access to actions on a node"
    DOMAIN_ADMIN = 4
    "For full access"


class GroupMembershipValidator(RequestPermissionValidator):
    """Permit actions based on group membership."""

    allowed_groups: List[AccountGroup]

    def __call__(self, request: List[str], context: Dict) -> bool:
        """Permit the action if the request comes from an account which belongs to the right group."""
        # if context request source is part of any groups mentioned in self.allow_groups, return true, otherwise false
        if not context:
            return False
        requestor_groups: List[str] = context["request_source"]["groups"]
        for allowed_group in self.allowed_groups:
            if allowed_group.name in requestor_groups:
                return True
        return False

    @property
    def fail_message(self) -> str:
        """Message that is reported when a request is rejected by this validator."""
        return "User does not belong to group"


class DomainController(SimComponent):
    """Main object for controlling the domain."""

    # owned objects
    accounts: Dict[str, Account] = {}
    groups: Final[List[AccountGroup]] = list(AccountGroup)

    domain_group_membership: Dict[Literal[AccountGroup.DOMAIN_ADMIN, AccountGroup.DOMAIN_USER], List[Account]] = {}
    local_group_membership: Dict[
        Tuple[temp_node, Literal[AccountGroup.LOCAL_ADMIN, AccountGroup.LOCAL_USER]], List[Account]
    ] = {}

    # references to non-owned objects. Not sure if all are needed here.
    nodes: Dict[str, temp_node] = {}
    applications: Dict[str, temp_application] = {}
    folders: List[temp_folder] = {}
    files: List[temp_file] = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        rm = super()._init_request_manager()
        # Action 'account' matches requests like:
        # ['account', '<account-uuid>', *account_action]
        rm.add_request(
            "account",
            RequestType(
                func=lambda request, context: self.accounts[request.pop(0)].apply_request(request, context),
                # TODO: not sure what should get returned here, revisit
                validator=GroupMembershipValidator(allowed_groups=[AccountGroup.DOMAIN_ADMIN]),
            ),
        )
        return rm

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update({"accounts": {acct.username: acct.describe_state() for acct in self.accounts.values()}})
        return state

    def _register_account(self, account: Account) -> None:
        """TODO."""
        ...

    def _deregister_account(self, account: Account) -> None:
        """TODO."""
        ...

    def create_account(self, username: str, password: str, account_type: AccountType) -> Account:
        """TODO."""
        ...

    def delete_account(self, account: Account) -> None:
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

    def check_account_permissions(self, account: Account, node: temp_node) -> List[AccountGroup]:
        """Return a list of permission groups that this account has on this node."""
        ...

    def register_node(self, node: temp_node) -> None:
        """TODO."""
        ...

    def deregister_node(self, node: temp_node) -> None:
        """TODO."""
        ...
