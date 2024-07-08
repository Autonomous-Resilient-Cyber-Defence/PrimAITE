# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
from typing import Dict, Optional

from prettytable import MARKDOWN, PrettyTable
from pydantic import Field

from primaite.simulator.core import SimComponent
from primaite.simulator.network.transmission.network_layer import IPProtocol
from primaite.simulator.network.transmission.transport_layer import Port
from primaite.simulator.system.services.service import Service


class User(SimComponent):
    """
    Represents a user in the PrimAITE system.

    :param username: The username of the user
    :param password: The password of the user
    :param disabled: Boolean flag indicating whether the user is disabled
    :param is_admin: Boolean flag indicating whether the user has admin privileges
    """

    username: str
    password: str
    disabled: bool = False
    is_admin: bool = False

    def describe_state(self) -> Dict:
        """
        Returns a dictionary representing the current state of the user.

        :return: A dict containing the state of the user
        """
        return self.model_dump()


class UserManager(Service):
    """
    Manages users within the PrimAITE system, handling creation, authentication, and administration.

    :param users: A dictionary of all users by their usernames
    :param admins: A dictionary of admin users by their usernames
    :param disabled_admins: A dictionary of currently disabled admin users by their usernames
    """

    users: Dict[str, User] = Field(default_factory=dict)
    admins: Dict[str, User] = Field(default_factory=dict)
    disabled_admins: Dict[str, User] = Field(default_factory=dict)

    def __init__(self, **kwargs):
        """
        Initializes a UserManager instanc.

        :param username: The username for the default admin user
        :param password: The password for the default admin user
        """
        kwargs["name"] = "UserManager"
        kwargs["port"] = Port.NONE
        kwargs["protocol"] = IPProtocol.NONE
        super().__init__(**kwargs)
        self.start()

    def describe_state(self) -> Dict:
        """
        Returns the state of the UserManager along with the number of users and admins.

        :return: A dict containing detailed state information
        """
        state = super().describe_state()
        state.update({"total_users": len(self.users), "total_admins": len(self.admins) + len(self.disabled_admins)})
        return state

    def show(self, markdown: bool = False):
        """
        Display the Users.

        :param markdown: Whether to display the table in Markdown format or not. Default is `False`.
        """
        table = PrettyTable(["Username", "Admin", "Enabled"])
        if markdown:
            table.set_style(MARKDOWN)
        table.align = "l"
        table.title = f"{self.sys_log.hostname} User Manager)"
        for user in self.users.values():
            table.add_row([user.username, user.is_admin, user.disabled])
        print(table.get_string(sortby="Username"))

    def _is_last_admin(self, username: str) -> bool:
        return username in self.admins and len(self.admins) == 1

    def add_user(
        self, username: str, password: str, is_admin: bool = False, bypass_can_perform_action: bool = False
    ) -> bool:
        """
        Adds a new user to the system.

        :param username: The username for the new user
        :param password: The password for the new user
        :param is_admin: Flag indicating if the new user is an admin
        :return: True if user was successfully added, False otherwise
        """
        if not bypass_can_perform_action and not self._can_perform_action():
            return False
        if username in self.users:
            return False
        user = User(username=username, password=password, is_admin=is_admin)
        self.users[username] = user
        if is_admin:
            self.admins[username] = user
        self.sys_log.info(f"{self.name}: Added new {'admin' if is_admin else 'user'}: {username}")
        return True

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticates a user's login attempt.

        :param username: The username of the user trying to log in
        :param password: The password provided by the user
        :return: The User object if authentication is successful, None otherwise
        """
        if not self._can_perform_action():
            return None
        user = self.users.get(username)
        if user and not user.disabled and user.password == password:
            self.sys_log.info(f"{self.name}: User authenticated: {username}")
            return user
        self.sys_log.info(f"{self.name}: Authentication failed for: {username}")
        return None

    def change_user_password(self, username: str, current_password: str, new_password: str) -> bool:
        """
        Changes a user's password.

        :param username: The username of the user changing their password
        :param current_password: The current password of the user
        :param new_password: The new password for the user
        :return: True if the password was changed successfully, False otherwise
        """
        if not self._can_perform_action():
            return False
        user = self.users.get(username)
        if user and user.password == current_password:
            user.password = new_password
            self.sys_log.info(f"{self.name}: Password changed for {username}")
            return True
        self.sys_log.info(f"{self.name}: Password change failed for {username}")
        return False

    def disable_user(self, username: str) -> bool:
        """
        Disables a user account, preventing them from logging in.

        :param username: The username of the user to disable
        :return: True if the user was disabled successfully, False otherwise
        """
        if not self._can_perform_action():
            return False
        if username in self.users and not self.users[username].disabled:
            if self._is_last_admin(username):
                self.sys_log.info(f"{self.name}: Cannot disable User {username} as they are the only enabled admin")
                return False
            self.users[username].disabled = True
            self.sys_log.info(f"{self.name}: User disabled: {username}")
            if username in self.admins:
                self.disabled_admins[username] = self.admins.pop(username)
            return True
        self.sys_log.info(f"{self.name}: Failed to disable user: {username}")
        return False

    def enable_user(self, username: str) -> bool:
        """
        Enables a previously disabled user account.

        :param username: The username of the user to enable
        :return: True if the user was enabled successfully, False otherwise
        """
        if not self._can_perform_action():
            return False
        if username in self.users and self.users[username].disabled:
            self.users[username].disabled = False
            self.sys_log.info(f"{self.name}: User enabled: {username}")
            if username in self.disabled_admins:
                self.admins[username] = self.disabled_admins.pop(username)
            return True
        self.sys_log.info(f"{self.name}: Failed to enable user: {username}")
        return False
