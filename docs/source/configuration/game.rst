.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK


``game``
========
This section defines high-level settings that apply across the game, currently it's used to help shape the action and observation spaces by restricting which ports and internet protocols should be considered. Here, users can also set the maximum number of steps in an episode.

``game`` hierarchy
------------------

.. code-block:: yaml

    game:
        max_episode_length: 256
        ports:
            - ARP
            - DNS
            - HTTP
            - POSTGRES_SERVER
        protocols:
            - ICMP
            - TCP
            - UDP
        thresholds:
            nmne:
                high: 10
                medium: 5
                low: 0
        seed: 1

``max_episode_length``
----------------------

Optional. Default value is ``256``.

The maximum number of episodes a Reinforcement Learning agent(s) can be trained for.

``ports``
---------

A list of ports that the Reinforcement Learning agent(s) are able to see in the observation space.

See :py:const:`primaite.utils.validation.port.PORT_LOOKUP` for a list of ports.

``protocols``
-------------

A list of protocols that the Reinforcement Learning agent(s) are able to see in the observation space.

See :py:const:`primaite.utils.validation.ip_protocol.PROTOCOL_LOOKUP` for a list of protocols.

``thresholds``
--------------

These are used to determine the thresholds of high, medium and low categories for counted observation occurrences.

``seed``
--------

Used to configure the random seeds used within PrimAITE, ensuring determinism within episode/session runs. If empty or set to -1, no seed is set. The given seed value is logged (by default) in ``primaite/<VERSION>/sessions/<DATE>/<TIME>/simulation_output``.
