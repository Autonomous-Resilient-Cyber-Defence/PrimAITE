.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Request System
==============

``SimComponent`` objects in the simulation are decoupled from the agent training logic. However, they still need a managed means of accepting requests to perform actions. For this, they use ``RequestManager`` and ``RequestType``.

Just like other aspects of SimComponent, the request types are not managed centrally for the whole simulation, but instead they are dynamically created and updated based on the nodes, links, and other components that currently exist. This was achieved in the following way:

- API
    A ``RequestType`` contains two elements:

    1. ``request`` - selects which action you want to take on this ``SimComponent``. This is formatted as a list of strings such as `['network', 'node', '<node-uuid>', 'service', '<service-uuid>', 'restart']`.
    2. ``context`` - optional extra information that can be used to decide how to process the request. This is formatted as a dictionary. For example, if the request requires authentication, the context can include information about the user that initiated the request to decide if their permissions are sufficient.

- request
    The request is a list of strings which help specify who should handle the request. The strings in the request list help RequestManagers traverse the 'ownership tree' of SimComponent. The example given above would be handled in the following way:

    1. ``Simulation`` receives `['network', 'node', '<node-uuid>', 'service', '<service-uuid>', 'restart']`.
        The first element of the request is ``network``, therefore it passes the request down to its network.
    2. ``Network`` receives `['node', '<node-uuid>', 'service', '<service-uuid>', 'restart']`.
        The first element of the request is ``node``, therefore the network looks at the node uuid and passes the request down to the node with that uuid.
    3. ``Node`` receives `['service', '<service-uuid>', 'restart']`.
        The first element of the request is ``service``, therefore the node looks at the service uuid and passes the rest of the request to the service with that uuid.
    4. ``Service`` receives ``['restart']``.
        Since ``restart`` is a defined request type in the service's own RequestManager, the service performs a restart.

Technical Detail
----------------

This system was achieved by implementing two classes, :py:class:`primaite.simulator.core.RequestType`, and :py:class:`primaite.simulator.core.RequestManager`.

``RequestType``
------

The ``RequestType`` object stores a reference to a method that executes the request, for example a node could have a request type that stores a reference to ``self.turn_on()``. Technically, this can be any callable that accepts `request, context` as it's parameters. In practice, this is often defined using ``lambda`` functions within a component's ``self._init_request_manager()`` method. Optionally, the ``RequestType`` object can also hold a validator that will permit/deny the request depending on context.

``RequestManager``
------------------

The ``RequestManager`` object stores a mapping between strings and request types. It is responsible for processing the request and passing it down the ownership tree. Technically, the ``RequestManager`` is itself a callable that accepts `request, context` tuple, and so it can be chained with other request managers.

A simple example without chaining can be seen in the :py:class:`primaite.simulator.file_system.file_system.File` class.

.. code-block:: python

    class File(FileSystemItemABC):
        ...
        def _init_request_manager(self):
            ...
            request_manager.add_request("scan", RequestType(func=lambda request, context: self.scan()))
            request_manager.add_request("repair", RequestType(func=lambda request, context: self.repair()))
            request_manager.add_request("restore", RequestType(func=lambda request, context: self.restore()))

*ellipses (``...``) used to omit code impertinent to this explanation*

Chaining RequestManagers
-----------------------

A request function needs to be a callable that accepts ``request, context`` as parameters. Since the request manager resolves requests by invoking it with ``request, context`` as parameter, it is possible to use a ``RequestManager`` as a ``RequestType``.

When a RequestManager accepts a request, it pops the first element and uses it to decide where it should send the remaining request. This is how PrimAITE traverses the ownership tree. If the ``RequestType`` has another ``RequestManager`` as its function, the request will be routed again. Each time the request is passed to a new request manager, the first element is popped.

An example of how this works is in the :py:class:`primaite.simulator.network.hardware.base.Node` class.

.. code-block:: python

    class Node(SimComponent):
        ...
        def _init_request_manager(self):
            ...
            # a regular action which is processed by the Node itself
            request_manager.add_request("turn_on", RequestType(func=lambda request, context: self.turn_on()))

            # if the Node receives a request where the first word is 'service', it will use a dummy manager
            # called self._service_request_manager to pass on the reqeust to the relevant service. This dummy
            # manager is simply here to map the service UUID that that service's own action manager. This is
            # done because the next string after "service" is always the uuid of that service, so we need an
            # RequestManager to pop that string before sending it onto the relevant service's RequestManager.
            self._service_request_manager = RequestManager()
            request_manager.add_request("service", RequestType(func=self._service_request_manager))
            ...

        def install_service(self, service):
            self.services[service.uuid] = service
            ...
            # Here, the service UUID is registered to allow passing actions between the node and the service.
            self._service_request_manager.add_request(service.uuid, RequestType(func=service._request_manager))
