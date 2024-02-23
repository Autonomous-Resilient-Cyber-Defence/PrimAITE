.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

``applications``
----------------

List of available applications that can be installed on a |NODE| can be found in :ref:`List of Applications <List of Applications>`

application in configuration
""""""""""""""""""""""""""""

Applications takes a list of applications as shown in the example below.

.. code-block:: yaml

    - ref: client_1
    hostname: client_1
    type: computer
    ...
    applications:
        - ref: example_application
        type: example_application_type
        options:
            # this section is different for each application
