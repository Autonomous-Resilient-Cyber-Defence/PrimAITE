from typing import Dict

from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.domain.controller import DomainController
from primaite.simulator.network.container import NetworkContainer


class Simulation(SimComponent):
    """TODO."""

    network: NetworkContainer
    domain: DomainController

    def __init__(self, **kwargs):
        if not kwargs.get("network"):
            kwargs["network"] = NetworkContainer()

        if not kwargs.get("domain"):
            kwargs["domain"] = DomainController()

        super().__init__(**kwargs)

        self.action_manager = ActionManager()
        # pass through network actions to the network objects
        self.action_manager.add_action(
            "network",
            Action(
                func=lambda request, context: self.network.apply_action(request, context), validator=AllowAllValidator()
            ),
        )
        # pass through domain actions to the domain object
        self.action_manager.add_action(
            "domain",
            Action(
                func=lambda request, context: self.domain.apply_action(request, context), validator=AllowAllValidator()
            ),
        )

    def describe_state(self) -> Dict:
        """
        Produce a dictionary describing the current state of this object.

        Please see :py:meth:`primaite.simulator.core.SimComponent.describe_state` for a more detailed explanation.

        :return: Current state of this object and child objects.
        :rtype: Dict
        """
        state = super().describe_state()
        state.update(
            {
                "network": self.network.describe_state(),
                "domain": self.domain.describe_state(),
            }
        )
        return state
