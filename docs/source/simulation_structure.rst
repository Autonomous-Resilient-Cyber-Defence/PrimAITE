.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK


Simulation Structure
====================

The simulation is made up of many smaller components which are related to each other in a tree-like structure. At the
top level, there is the :py:meth:`primaite.simulator.sim_container.Simulation`, which keeps track of the physical network
and a domain controller for managing software and users.

Each node of the simulation 'tree' has responsibility for creating, deleting, and updating its direct descendants. Also,
when a component's ``describe_state()`` method is called, it will include the state of its descendants. The
``apply_request()`` method can be used to act on a component or one of its descendants. The diagram below shows the
relationship between components.

.. image:: ../../_static/component_relationship.png
    :width: 500
    :align: center
    :alt: ::    The top level simulation object owns a NetworkContainer and a DomainController. The DomainController has a
                list of accounts. The network container has links and nodes. Nodes can own switchports, NICs, FileSystem,
                Application, Service, and Process.


Actions
=======
Agents can interact with the simulation by using actions. Actions are standardised with the
:py:class:`primaite.simulation.core.RequestType` class, which just holds a reference to two special functions.

1. The request function itself, it must accept a `request` parameters which is a list of strings that describe what the
   action should do. It must also accept a `context` dict which can house additional information surrounding the action.
   For example, the context will typically include information about which entity intiated the action.
2. A validator function. This function should return a boolean value that decides if the request is permitted or not.
   It uses the same paramters as the action function.

Action Permissions
------------------
When an agent tries to perform an action on a simulation component, that action will only be executed if the request is
validated. For example, some actions can require that an agent is logged into an admin account. Each action defines its
own permissions using an instance of :py:class:`primaite.simulation.core.ActionPermissionValidator`. The below code
snippet demonstrates usage of the ``ActionPermissionValidator``.

.. code:: python

    from primaite.simulator.core import Action, RequestManager, SimComponent
    from primaite.simulator.domain.controller import AccountGroup, GroupMembershipValidator

    class Smartphone(SimComponent):
        name: str
        apps = []

        def _init_request_manager(self) -> RequestManager:
            am = super()._init_request_manager()
            am.add_request(
                "reset_factory_settings",
                Action(
                    func = lambda request, context: self.reset_factory_settings(),
                    validator = GroupMembershipValidator([AccountGroup.DOMAIN_ADMIN]),
                )
            )

        def reset_factory_settings(self):
            self.apps = []

    phone = Smartphone(name="phone1")

    # try to wipe the phone as a domain user, this will have no effect
    phone.apply_action(["reset_factory_settings"], context={"request_source":{"groups":["DOMAIN_USER"]})

    # try to wipe the phone as an admin user, this will wipe the phone
    phone.apply_action(["reset_factory_settings"], context={"request_source":{"groups":["DOMAIN_ADMIN"]})
