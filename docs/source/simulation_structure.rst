.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK


Simulation Structure
====================

The simulation is made up of many smaller components which are related to each other in a tree-like structure. At the
top level, there is an object called the ``SimulationController`` _(doesn't exist yet)_, which has a physical network
and a software controller for managing software and users.

Each node of the simulation 'tree' has responsibility for creating, deleting, and updating its direct descendants.
