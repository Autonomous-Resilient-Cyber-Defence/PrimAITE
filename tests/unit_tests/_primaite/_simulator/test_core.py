from typing import Callable, Dict, List, Literal, Tuple

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

        comp = TestComponent(name="computer", size=(5, 10))
        dump = comp.model_dump()
        assert dump["name"] is "computer"

    def test_apply_action(self):
        """Validate that we can override apply_action behaviour and it updates the state of the component."""

        class TestComponent(SimComponent):
            name: str
            status: Literal["on", "off"] = "off"

            def describe_state(self) -> Dict:
                return {}

            def _possible_actions(self) -> Dict[str, Callable[[List[str]], None]]:
                return {
                    "turn_off": self._turn_off,
                    "turn_on": self._turn_on,
                }

            def _turn_off(self, options: List[str]) -> None:
                assert len(options) == 0, "This action does not support options."
                self.status = "off"

            def _turn_on(self, options: List[str]) -> None:
                assert len(options) == 0, "This action does not support options."
                self.status = "on"

        comp = TestComponent(name="computer", status="off")

        assert comp.status == "off"
        comp.apply_action(["turn_on"])
        assert comp.status == "on"

        with pytest.raises(ValueError):
            comp.apply_action(["do_nothing"])
