from typing import Dict

from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.domain.controller import DomainController
from primaite.simulator.network.container import Network


class Simulation(SimComponent):
    """Top-level simulation object which holds a reference to all other parts of the simulation."""

    network: Network
    domain: DomainController

    def __init__(self, **kwargs):
        """Initialise the Simulation."""
        if not kwargs.get("network"):
            kwargs["network"] = Network()

        if not kwargs.get("domain"):
            kwargs["domain"] = DomainController()

        super().__init__(**kwargs)

    def _init_action_manager(self) -> ActionManager:
        am = super()._init_action_manager()
        # pass through network actions to the network objects
        am.add_action("network", Action(func=self.network._action_manager))
        # pass through domain actions to the domain object
        am.add_action("domain", Action(func=self.domain._action_manager))
        am.add_action("do_nothing", Action(func=lambda request, context: ()))
        return am

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
