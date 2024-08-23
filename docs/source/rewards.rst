.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

Rewards
#######

Rewards in PrimAITE are based on a system of individual components that react to events in the simulation. An agent's reward function is calculated as the weighted sum of several reward components.

Components
**********
The following API pages describe the use of each reward component and the possible configuration options. An example of configuring each via yaml is also provided.

:py:class:`primaite.game.agent.rewards.DummyReward`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: DUMMY
              weight: 1.0


:py:class:`primaite.game.agent.rewards.DatabaseFileIntegrity`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: DATABASE_FILE_INTEGRITY
              weight: 1.0
              options:
                node_hostname: server_1
                folder_name: database
                file_name: database.db


:py:class:`primaite.game.agent.rewards.WebServer404Penalty`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: WEB_SERVER_404_PENALTY
              node_hostname: web_server
              weight: 1.0
              options:
                service_name: WebService
                sticky: false


:py:class:`primaite.game.agent.rewards.WebpageUnavailablePenalty`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: WEBPAGE_UNAVAILABLE_PENALTY
              node_hostname: computer_1
              weight: 1.0
              options:
                sticky: false


:py:class:`primaite.game.agent.rewards.GreenAdminDatabaseUnreachablePenalty`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: GREEN_ADMIN_DATABASE_UNREACHABLE_PENALTY
              weight: 1.0
              options:
                node_hostname: admin_pc_1
                sticky: false


:py:class:`primaite.game.agent.rewards.SharedReward`

.. code-block:: yaml

    agents:
      - ref: scripted_agent
        # ...
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: SHARED_REWARD
              weight: 1.0
              options:
                agent_name: scripted_agent


:py:class:`primaite.game.agent.rewards.ActionPenalty`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
            - type: ACTION_PENALTY
              weight: 1.0
              options:
                  action_penalty: -0.3
                  do_nothing_penalty: 0.0
