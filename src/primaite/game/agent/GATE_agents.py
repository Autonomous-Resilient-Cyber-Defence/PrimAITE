from primaite.game.agent.interface import AbstractGATEAgent
from arcd_gate.client.gate_client import GATEClient


class GATEMan(GATEClient):

    @property
    def rl_framework(self) -> str:
        return "SB3"

    @property
    def rl_framework(self) -> str:
        pass

    @property
    def rl_algorithm(self) -> str:
        pass

    @property
    def seed(self) -> Optional[int]:
        return None

    @property
    def n_learn_episodes(self) -> int:
        return 0

    @property
    def n_learn_steps(self) -> int:
        return 0

    @property
    def n_eval_episodes(self) -> int:
        return 0

    @property
    def n_eval_steps(self) -> int:
        return 0

    @property
    def action_space(self) -> spaces.Space:
        pass

    @property
    def observation_space(self) -> spaces.Space:
        pass

    def step(self, action: ActType) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        pass

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict[str, Any]] = None) -> Tuple[np.ndarray, Dict]:
        pass

    def close(self):
        pass

class GATERLAgent(AbstractGATEAgent):
    ...
    # The communication with GATE needs to be handled by the PrimaiteSession, rather than by individual agents,
    # because when we are supporting MARL, the actions form multiple agents will have to be batched

    # For example MultiAgentEnv in Ray allows sending a dict of observations of multiple agents, then it will reply
    # with the actions for those agents.


