.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Actions System
==============

`SimComponent`s in the simulation are decoupled from the agent training logic. However, they still need a managed means of accepting requests to perform actions. For this, they use `ActionManager` and `Action`.

Just like other aspects of SimComponent, the actions are not managed centrally for the whole simulation, but instead they are dynamically created and updated based on the nodes, links, and other components that currently exist. This was achieved with the following design decisions:

- API
    An 'action' contains two elements:

    1. `request` - selects which action you want to take on this `SimComponent`. This is formatted as a list of strings such as `['network', 'node', '<node-uuid>', 'service', '<service-uuid>', 'restart']`.
    2. `context` - optional extra information that can be used to decide how to process the action. This is formatted as a dictionary. For example, if the action requires authentication, the context can include information about the user that initiated the request to decide if their permissions are sufficient.

- request
    The request is a list of strings which help specify who should handle the request. The strings in the request list help ActionManagers traverse the 'ownership tree' of SimComponent. The example given above would be handled in the following way:

    1. `Simulation` receives `['network', 'node', '<node-uuid>', 'service', '<service-uuid>', 'restart']`.
        The first element of the action is `network`, therefore it passes the action down to its network.
    2. `Network` receives `['node', '<node-uuid>', 'service', '<service-uuid>', 'restart']`.
        The first element of the action is `node`, therefore the network looks at the node uuid and passes the action down to the node with that uuid.
    3. `Node` receives `['service', '<service-uuid>', 'restart']`.
        The first element of the action is `service`, therefore the node looks at the service uuid and passes the rest of the action to the service with that uuid.
    4. `Service` receives `['restart']`.
        Since `restart` is a defined action in the service's own ActionManager, the service performs a restart.

Techincal Detail
================

This system was achieved by implementing two classes, :py:class:`primaite.simulator.core.Action`, and :py:class:`primaite.simulator.core.ActionManager`.

Action
------

The `Action` object stores a reference to a method that performs the action, for example a node could have an action that stores a reference to `self.turn_on()`. Techincally, this can be any callable that accepts `request, context` as it's parameters. In practice, this is often defined using `lambda` functions within a component's `self._init_action_manager()` method. Optionally, the `Action` object can also hold a validator that will permit/deny the action depending on context.

ActionManager
-------------

The `ActionManager` object stores a mapping between strings and actions. It is responsible for processing the `request` and passing it down the ownership tree. Techincally, the `ActionManager` is itself a callable that accepts `request, context` tuple, and so it can be chained with other action managers.

A simple example without chaining can be seen in the :py:class:`primaite.simulator.file_system.file_system.File` class.

.. code-block:: python

    class File(FileSystemItemABC):
        ...
        def _init_action_manager(self):
            ...
            action_manager.add_action("scan", Action(func=lambda request, context: self.scan()))
            action_manager.add_action("repair", Action(func=lambda request, context: self.repair()))
            action_manager.add_action("restore", Action(func=lambda request, context: self.restore()))

*ellipses (`...`) used to omit code impertinent to this explanation*

Chaining ActionManagers
-----------------------

Since the  method for performing an action needs to accept `request, context` as parameters, and ActionManager itself is a callable that accepts `request, context` as parameters, it possible to use ActionManager as an action. In fact, that is how PrimAITE deals with traversing the ownership tree. Each time an ActionManager accepts a request, it pops the first elements and uses it to decide to which Action it should send the remaining request. However, the Action could have another ActionManager as it's function, therefore the request will be routed again. Each time the request is passed to a new action manager, the first element is popped.

An example of how this works is in the :py:class:`primaite.simulator.network.hardware.base.Node` class.

.. code-block:: python

    class Node(SimComponent):
        ...
        def _init_action_manager(self):
            ...
            # a regular action which is processed by the Node itself
            action_manager.add_action("turn_on", Action(func=lambda request, context: self.turn_on()))

            # if the Node receives a request where the first word is 'service', it will use a dummy manager
            # called self._service_action_manager to pass on the reqeust to the relevant service. This dummy
            # manager is simply here to map the service UUID that that service's own action manager. This is
            # done because the next string after "service" is always the uuid of that service, so we need an
            # actionmanager to pop that string before sending it onto the relevant service's ActionManager.
            self._service_action_manager = ActionManager()
            action_manager.add_action("service", Action(func=self._service_action_manager))
            ...

        def install_service(self, service):
            self.services[service.uuid] = service
            ...
            # Here, the service UUID is registered to allow passing actions between the node and the service.
            self._service_action_manager.add_action(service.uuid, Action(func=service._action_manager))
