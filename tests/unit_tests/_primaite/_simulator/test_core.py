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
        dump = comp.model_dump_json()
        reconstructed = TestComponent.model_validate_json(dump)
        assert dump == reconstructed.model_dump_json()
