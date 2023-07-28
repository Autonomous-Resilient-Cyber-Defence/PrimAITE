from typing import Dict, List, Literal, Tuple

import pytest
from pydantic import ValidationError

from primaite.simulator.core import SimComponent


class TestIsolatedSimComponent:
    """Test the SimComponent class in isolation."""

    def test_data_validation(self):
        """
        Test that our derived class does not interfere with pydantic data validation.

        This test may seem like it's simply validating pydantic data validation, but
        actually it is here to give us assurance that any custom functionality we add
        to the SimComponent does not interfere with pydantic.
        """

        class TestComponent(SimComponent):
            name: str
            size: Tuple[float, float]

            def describe_state(self) -> Dict:
                return {}

            def apply_action(self, action: List[str]) -> None:
                pass

        comp = TestComponent(name="computer", size=(5, 10))
        assert isinstance(comp, TestComponent)

        with pytest.raises(ValidationError):
            invalid_comp = TestComponent(name="computer", size="small")  # noqa

    def test_serialisation(self):
        """Validate that our added functionality does not interfere with pydantic."""

        class TestComponent(SimComponent):
            name: str
            size: Tuple[float, float]

            def describe_state(self) -> Dict:
                return {}

            def apply_action(self, action: List[str]) -> None:
                pass

        comp = TestComponent(name="computer", size=(5, 10))
        dump = comp.model_dump()
        assert dump == {"name": "computer", "size": (5, 10)}

    def test_apply_action(self):
        """Validate that we can override apply_action behaviour and it updates the state of the component."""

        class TestComponent(SimComponent):
            name: str
            status: Literal["on", "off"] = "off"

            def describe_state(self) -> Dict:
                return {}

            def apply_action(self, action: List[str]) -> None:
                possible_actions = {
                    "turn_off": self._turn_off,
                    "turn_on": self._turn_on,
                }
                if action[0] in possible_actions:
                    possible_actions[action[0]](action[1:])
                else:
                    raise ValueError(f"{self} received invalid action {action}")

            def _turn_off(self):
                self.status = "off"

            def _turn_on(self):
                self.status = "on"

        comp = TestComponent(name="computer", status="off")

        assert comp.status == "off"
        comp.apply_action(["turn_on"])
        assert comp.status == "on"

        with pytest.raises(ValueError):
            comp.apply_action(["do_nothing"])
