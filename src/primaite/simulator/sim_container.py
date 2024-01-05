from typing import Dict

from primaite.simulator.core import RequestManager, RequestType, SimComponent
from primaite.simulator.domain.controller import DomainController
from primaite.simulator.network.container import Network


class Simulation(SimComponent):
    """Top-level simulation object which holds a reference to all other parts of the simulation."""

    network: Network
    # domain: DomainController

    def __init__(self, **kwargs):
        """Initialise the Simulation."""
        if not kwargs.get("network"):
            kwargs["network"] = Network()

        if not kwargs.get("domain"):
            kwargs["domain"] = DomainController()

        super().__init__(**kwargs)

    def set_original_state(self):
        """Sets the original state."""
        self.network.set_original_state()

    def reset_component_for_episode(self, episode: int):
        """Reset the original state of the SimComponent."""
        self.network.reset_component_for_episode(episode)

    def _init_request_manager(self) -> RequestManager:
        rm = super()._init_request_manager()
        # pass through network requests to the network objects
        rm.add_request("network", RequestType(func=self.network._request_manager))
        # pass through domain requests to the domain object
        rm.add_request("domain", RequestType(func=self.domain._request_manager))
        rm.add_request("do_nothing", RequestType(func=lambda request, context: ()))
        return rm

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

    def apply_timestep(self, timestep: int) -> None:
        """Apply a timestep to the simulation."""
        super().apply_timestep(timestep)
        self.network.apply_timestep(timestep)
