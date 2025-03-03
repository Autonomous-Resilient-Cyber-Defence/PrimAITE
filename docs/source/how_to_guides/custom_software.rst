.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _custom_software:

Creating Custom Software for PrimAITE
*************************************

This page aims to provide a how-to guide on how to create your own custom software for use within PrimAITE.

PrimAITE has a base software class which should be inherited from when building custom software. Examples of this can be seen in the ``IOSoftware`` and ``Process`` classes.
It's important that any new software created within PrimAITE has the ``identifier`` attribute defined, for use when generating the environment.

Some default attributes may need to be adjusted to align with the intended application of the custom software.


.. code:: Python

    from src.primaite.simulator.system.software import Software

    class CustomSoftware(Software, identifier="CustomSoftware"):
        """
        An example of Custom Software within PrimAITE.
        """

        operating_state: OperatingState
        "The current operating state of the Custom software"

        def describe_state(self) -> Dict:
            """
            Produce a dictionary describing the current state of this object.

            :return: Current state of this object and child objects.
            :rtype: Dict
            """
            state = super().describe_state()
            state.update({"operating_state": self.operating_state.value})

Default Install
###############

Software can be set to auto-install onto a Node by adding it to the ``SYSTEM_SOFTWARE`` dictionary for the node. An example can be seen in the ``HostNode`` class, which pre-installs some key software that is expected on Nodes, such as the ``NTPClient`` and ``UserManager``.

Requirements
############

Any custom software will need to provide an implementation of the ``describe_state`` method, and conform to the general Pydantic requirements.
It's a good idea, if possible, to also create a ``.show()`` method, as this can be used for visualising the software's status when developing within PrimAITE.

Interaction with the PrimAITE Request System
############################################

If the software is intended to be used by an agent via a :ref:`custom_action`, then it will likely need an implementation of the ``RequestManager``.
Detailed information about the PrimAITE request system can be seen in :ref:`request_system`. An example implementation, derived from the `Application` class is seen below:

.. code:: Python

    def _init_request_manager(self) -> RequestManager:
        """
        Initialise the request manager.

        More information in user guide and docstring for SimComponent._init_request_manager.
        """
        _is_application_running = Application._StateValidator(application=self, state=ApplicationOperatingState.RUNNING)

        rm = super()._init_request_manager()
        rm.add_request(
            "scan",
            RequestType(
                func=lambda request, context: RequestResponse.from_bool(self.scan()), validator=_is_application_running
            ),
        )
        return rm


Further information
###################

For more detailed information about the implementation of software within PrimAITE, see :ref:`software`.
