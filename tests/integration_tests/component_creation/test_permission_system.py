from enum import Enum
from typing import Dict, List, Literal

import pytest

from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.domain.controller import AccountGroup, GroupMembershipValidator


def test_group_action_validation() -> None:
    """Check that actions are denied when an unauthorised request is made."""

    class Folder(SimComponent):
        name: str

        def describe_state(self) -> Dict:
            return super().describe_state()

    class Node(SimComponent):
        name: str
        folders: List[Folder] = []

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.action_manager = ActionManager()

            self.action_manager.add_action(
                "create_folder",
                Action(
                    func=lambda request, context: self.create_folder(request[0]),
                    validator=GroupMembershipValidator([AccountGroup.local_admin, AccountGroup.domain_admin]),
                ),
            )

        def describe_state(self) -> Dict:
            return super().describe_state()

        def create_folder(self, folder_name: str) -> None:
            new_folder = Folder(uuid="0000-0000-0001", name=folder_name)
            self.folders.append(new_folder)

        def remove_folder(self, folder: Folder) -> None:
            self.folders = [x for x in self.folders if x is not folder]

    permitted_context = {"request_source": {"agent": "BLUE", "account": "User1", "groups": ["local_admin"]}}

    my_node = Node(uuid="0000-0000-1234", name="pc")
    my_node.apply_action(["create_folder", "memes"], context=permitted_context)
    assert len(my_node.folders) == 1
    assert my_node.folders[0].name == "memes"

    invalid_context = {"request_source": {"agent": "BLUE", "account": "User1", "groups": ["local_user", "domain_user"]}}

    my_node.apply_action(["create_folder", "memes2"], context=invalid_context)
    assert len(my_node.folders) == 1
    assert my_node.folders[0].name == "memes"


def test_hierarchical_action_with_validation() -> None:
    """Check that validation works with sub-objects"""

    class Application(SimComponent):
        name: str
        state: Literal["on", "off", "disabled"] = "off"

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.action_manager = ActionManager()

            self.action_manager.add_action(
                "turn_on",
                Action(
                    func=lambda request, context: self.turn_on(),
                    validator=AllowAllValidator(),
                ),
            )
            self.action_manager.add_action(
                "turn_off",
                Action(
                    func=lambda request, context: self.turn_off(),
                    validator=AllowAllValidator(),
                ),
            )
            self.action_manager.add_action(
                "disable",
                Action(
                    func=lambda request, context: self.disable(),
                    validator=GroupMembershipValidator([AccountGroup.local_admin, AccountGroup.domain_admin]),
                ),
            )
            self.action_manager.add_action(
                "enable",
                Action(
                    func=lambda request, context: self.enable(),
                    validator=GroupMembershipValidator([AccountGroup.local_admin, AccountGroup.domain_admin]),
                ),
            )

        def describe_state(self) -> Dict:
            return super().describe_state()

        def disable(self) -> None:
            self.status = "disabled"

        def enable(self) -> None:
            if self.status == "disabled":
                self.status = "off"

        def turn_on(self) -> None:
            if self.status == "off":
                self.status = "on"

        def turn_off(self) -> None:
            if self.status == "on":
                self.status = "off"

    class Node(SimComponent):
        name: str
        state: Literal["on", "off"] = "on"
        apps: List[Application] = []

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.action_manager = ActionManager()

            self.action_manager.add_action(
                "apps",
                Action(
                    func=lambda request, context: self.send_action_to_app(request.pop(0), request, context),
                    validator=AllowAllValidator(),
                ),
            )

        def describe_state(self) -> Dict:
            return super().describe_state()

        def install_app(self, app_name: str) -> None:
            new_app = Application(name=app_name)
            self.apps.append(new_app)

        def send_action_to_app(self, app_name: str, options: List[str], context: Dict):
            for app in self.apps:
                if app_name == app.name:
                    app.apply_action(options)
                    break
            else:
                msg = f"Node has no app with name {app_name}"
                raise LookupError(msg)

    my_node = Node(name="pc")
    my_node.install_app("Chrome")
    my_node.install_app("Firefox")

    non_admin_context = {
        "request_source": {"agent": "BLUE", "account": "User1", "groups": ["local_user", "domain_user"]}
    }

    admin_context = {
        "request_source": {
            "agent": "BLUE",
            "account": "User1",
            "groups": ["local_admin", "domain_admin", "local_user", "domain_user"],
        }
    }

    my_node.apply_action(["apps", "Chrome", "disable"], non_admin_context)
    my_node.apply_action(["apps", "Firefox", "turn_on"], non_admin_context)

    assert my_node.apps[0].name == "Chrome"
    assert my_node.apps[1].name == "Firefox"
    assert my_node.apps[0].state == ...  # TODO: finish
