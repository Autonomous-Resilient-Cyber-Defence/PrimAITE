.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Simulation State
================

``SimComponent`` objects in the simulation have a method called ``describe_state`` which return a dictionary of the state of the component. This is used to report pertinent data that could impact an agent's actions or rewards. For instance, the name and health status of a node is reported, which can be used by a reward function to punish corrupted or compromised nodes and reward healthy nodes. Each ``SimComponent`` object reports not only its own attributes in the state but also those of its child components. I.e. a computer node will report the state of its ``FileSystem`` and the ``FileSystem`` will report the state of its files and folders. This happens by recursively calling the children's own ``describe_state`` methods.

The game layer calls ``describe_state`` on the trunk ``SimComponent`` (the top-level parent) and then passes the state to the agents once per simulation step. For this reason, all ``SimComponent`` objects must have a ``describe_state`` method, and they must all be linked to the trunk ``SimComponent``.

This code snippet demonstrates how the state information is defined within the ``SimComponent`` class:

.. code-block:: python

    class Node(SimComponent):
        operating_state: NodeOperatingState = NodeOperatingState.OFF
        services: Dict[str, Service] = {}

        def describe_state(self) -> Dict:
            state = super().describe_state()
            state["operating_state"] = self.operating_state.value
            state["services"] = {uuid: svc.describe_state() for uuid, svc in self.services.items()}
            return state

    class Service(SimComponent):
        health_state: ServiceHealthState = ServiceHealthState.GOOD
        def describe_state(self) -> Dict:
            state = super().describe_state()
            state["health_state"] = self.health_state.value
            return state
