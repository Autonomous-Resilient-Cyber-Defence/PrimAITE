# What do? Be an entry point for using PrimAITE
# 1. parse monoconfig
# 2. craete simulation
# 3. create actors and configure their actions/observations/rewards/ anything else
# 4. Create connection with ARCD GATE
# 5. idk

from primaite.simulator.sim_container import Simulation
from primaite.game.agent.interface import AbstractAgent

from typing import List

class PrimaiteSession:
    def __init__(self):
        self.simulation: Simulation = Simulation()
        self.agents:List[AbstractAgent] = []
        self.step_counter:int = 0
        self.episode_counter:int = 0


    def step(self):
        # currently designed with assumption that all agents act once per step in order


        for agent in self.agents:
            # 3. primaite session asks simulation to provide initial state
            # 4. primate session gives state to all agents
            # 5. primaite session asks agents to produce an action based on most recent state
            sim_state = self.simulation.describe_state()

            # 6. each agent takes most recent state and converts it to CAOS observation
            agent_obs = agent.get_obs_from_state(sim_state)

            # 7. meanwhile each agent also takes state and calculates reward
            agent_reward = agent.get_reward_from_state(sim_state)

            # 8. each agent takes observation and applies decision rule to observation to create CAOS
            #    action(such as random, rulebased, or send to GATE) (therefore, converting CAOS action
            #    to discrete(40) is only necessary for purposes of RL learning, therefore that bit of
            #    code should live inside of the GATE agent subclass)
            # gets action in CAOS format
            agent_action = agent.get_action(agent_obs, agent_reward)
            # 9. CAOS action is converted into request (extra information might be needed to enrich
            # the request, this is what the execution definition is there for)
            agent_request = agent.format_request(agent_action)

            # 10. primaite session receives the action from the agents and asks the simulation to apply each
            self.simulation.apply_action(agent_request)

        self.simulation.apply_timestep(self.step_counter)
        self.step_counter += 1

