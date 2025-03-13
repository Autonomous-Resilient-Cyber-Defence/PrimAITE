.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _Rewards:

Rewards
#######

Rewards in PrimAITE are based on a system of individual components that react to events in the simulation. An agent's reward function is calculated as the weighted sum of several reward components.

Some rewards, such as the ``green-admin-database-unreachable-penalty``, can be marked as 'sticky' in their configuration. Setting this to ``True`` will mean that they continue to output the same value after an event until another event of that type.
In the instance of the ``green-admin-database-unreachable-penalty``, the database admin reward will stay negative until the next successful database request is made, even if the database admin agents do nothing and the database returns a good state.

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
          - type: dummy
            weight: 1.0


:py:class:`primaite.game.agent.rewards.DatabaseFileIntegrity`

.. code-block:: yaml

    agents:
      - ref: agent_name
        # ...
        reward_function:
          reward_components:
          - type: database-file-integrity
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
          - type: web-server-404-penalty
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
          - type: webpage-unavailable-penalty
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
          - type: green-admin-database-unreachable-penalty
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
          - type: shared-reward
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
          - type: action-penalty
            weight: 1.0
            options:
                action_penalty: -0.3
                do_nothing_penalty: 0.0
