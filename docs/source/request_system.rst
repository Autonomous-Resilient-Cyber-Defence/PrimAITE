.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

Request System
**************

``SimComponent`` objects in the simulation are decoupled from the agent training logic. However, they still need a managed means of accepting requests to perform actions. For this, they use ``RequestManager`` and ``RequestType``.

Just like other aspects of SimComponent, the request types are not managed centrally for the whole simulation, but instead they are dynamically created and updated based on the nodes, links, and other components that currently exist in the simulation. This is achieved in the following way:

When requesting an action within the simulation, these two arguments must be provided:

1. ``request`` - selects which action you want to take on this ``SimComponent``. This is formatted as a list of strings such as ``['network', 'node', '<node-name>', 'service', '<service-name>', 'restart']``.
2. ``context`` - optional extra information that can be used to decide how to process the request. This is formatted as a dictionary. For example, if the request requires authentication, the context can include information about the user that initiated the request to decide if their permissions are sufficient.

When a request is resolved, it returns a success status, and optional additional data about the request.

``status`` can be one of:

* ``success``: the request was executed
* ``failure``: the request could not be executed
* ``unreachable``: the target for the request was not found
* ``pending``: the request was initiated, but has not finished during this step

``data`` can be a dictionary with any arbitrary JSON-like data to describe the outcome of the request.

Request Syntax:
"""""""""""""""

Request Syntax
---------------

The request is a list of strings which help specify who should handle the request. The strings in the request list help RequestManagers traverse the 'ownership tree' of SimComponent. The example given above would be handled in the following way:

1. ``Simulation`` receives ``['network', 'node', 'computer_1', 'service', 'DNSService', 'restart']``.
    The first element of the request is ``network``, therefore it passes the request down to its network.
2. ``Network`` receives ``['node', 'computer_1', 'service', 'DNSService', 'restart']``.
    The first element of the request is ``node``, therefore the network looks at the node name and passes the request down to the node with that name.
3. ``computer_1`` receives ``['service', 'DNSService', 'restart']``.
    The first element of the request is ``service``, therefore the node looks at the service name and passes the rest of the request to the service with that name.
4. ``DNSService`` receives ``['restart']``.
    Since ``restart`` is a defined request type in the service's own RequestManager, the service performs a restart.

- ``context``
    The context is not used by any of the currently implemented components or requests.

Request responses
-----------------

When the simulator receives a request, it returns a response with a success status. The possible statuses are:

* **success**: The request was received and successfully executed.
    * For example, the agent tries to add an ACL rule and specifies correct parameters, and the ACL rule is added successfully.

* **failure**: The request was received, but it could not be executed, or it failed while executing.
    * For example, the agent tries to execute the ``WebBrowser`` application, but the webpage wasn't retrieved because the DNS server is not setup on the node.

* **unreachable**: The request was sent to a simulation component that does not exist.
    * For example, the agent tries to scan a file that has not been created yet.

For more information, please refer to the ``Requests-and-Responses.ipynb`` jupyter notebook

Technical Detail
================

This system was achieved by implementing two classes, :py:class:`primaite.simulator.core.RequestType`, and :py:class:`primaite.simulator.core.RequestManager`.

``RequestType``
---------------

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
            request_manager.add_request("scan", RequestType(func=lambda request, context: RequestResponse.from_bool(self.scan())))
            request_manager.add_request("repair", RequestType(func=lambda request, context: RequestResponse.from_bool(self.repair())))
            request_manager.add_request("restore", RequestType(func=lambda request, context: RequestResponse.from_bool(self.restore())))

*ellipses (``...``) used to omit code impertinent to this explanation*

Chaining RequestManagers
------------------------

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
            # called self._service_request_manager to pass on the request to the relevant service. This dummy
            # manager is simply here to map the service name that that service's own action manager. This is
            # done because the next string after "service" is always the name of that service, so we need an
            # RequestManager to pop that string before sending it onto the relevant service's RequestManager.
            self._service_request_manager = RequestManager()
            request_manager.add_request("service", RequestType(func=self._service_request_manager))
            ...

        def install_service(self, service):
            self.services[service.name] = service
            ...
            # Here, the service name is registered to allow passing actions between the node and the service.
            self._service_request_manager.add_request(service.name, RequestType(func=service._request_manager))

This process is repeated until the request word corresponds to a callable function rather than another ``RequestManager`` .

Request Validation
------------------

There are times when a request should be rejected. For instance, if an agent attempts to run an application on a node that is currently off. For this purpose, requests are filtered by an object called a validator. :py:class:`primaite.simulator.core.RequestPermissionValidator` is a basic class whose ``__call__()`` method returns ``True`` if the request should be permitted or ``False`` if it cannot be permitted. For example, the Node class has a validator called :py:class:`primaite.simulator.network.hardware.base.Node._NodeIsOnValidator<_NodeIsOnValidator>` which allows requests only when the operating status of the node is ``ON``.

Requests that are specified without a validator automatically get assigned an ``AllowAllValidator`` which allows requests no matter what.

Request Response
----------------

The :py:class:`primaite.interface.request.RequestResponse<RequestResponse>` carries response data between the simulator and the game layer. The ``status`` field reports on the success or failure, and the ``data`` field is for any additional data. The most common way that this class is used is by the ``from_bool`` method. This way, given a True or False, a successful or failed request response is generated, respectively (with an empty data field).

For instance, the ``execute`` action on a :py:class:`primaite.simulator.system.applications.web_browser.WebBrowser<WebBrowser>` calls the ``get_webpage()`` method. ``get_webpage()`` returns a True if the webpage was successfully retrieved, and False if unsuccessful for any reason, such as being blocked by an ACL, or if the database server is unresponsive. The boolean returned from ``get_webpage()`` is used to create the request response with ``from_bool()``.

Just as the requests themselves were passed from owner to component, the request response is bubbled back up from component to owner until it arrives at the game layer.
