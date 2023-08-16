from primaite.simulator.core import Action, ActionManager, AllowAllValidator, SimComponent
from primaite.simulator.domain.controller import DomainController


class __TempNetwork:
    """TODO."""

    pass


class SimulationContainer(SimComponent):
    """TODO."""

    network: __TempNetwork
    domain: DomainController

    def __init__(self, **kwargs):
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
