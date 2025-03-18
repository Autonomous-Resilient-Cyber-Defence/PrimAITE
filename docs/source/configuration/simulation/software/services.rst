.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

``services``
------------

List of available services that can be installed on a |NODE| can be found in :ref:`List of Services <List of Services>`

services in configuration
"""""""""""""""""""""""""

Services takes a list of services as shown in the example below.

.. code-block:: yaml

    hostname: client_1
    type: computer
    ...
    applications:
        type: example_service_type
        options:
            # this section is different for each service
