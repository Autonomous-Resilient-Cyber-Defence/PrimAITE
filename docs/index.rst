.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Welcome to PrimAITE's documentation
====================================

What is PrimAITE?
------------------------

PrimAITE (Primary-level AI Training Environment) is a simulation environment for training AI under the ARCD programme. It incorporates the functionality required of a Primary-level environment, as specified in the Dstl ARCD Training Environment Matrix document:

* The ability to model a relevant platform / system context;
* The ability to model key characteristics of a platform / system by representing connections, IP addresses, ports, traffic loading, operating systems, file system, services and processes;
* Operates at machine-speed to enable fast training cycles.

PrimAITE aims to evolve into an ARCD environment that could be used as the follow-on from Reception level approaches (e.g. `Yawning-Titan <https://github.com/dstl/YAWNING-TITAN>`_), and help bridge the Sim-to-Real gap into Secondary level environments.

What is PrimAITE built with
--------------------------------------

* `OpenAI's Gym <https://gym.openai.com/>`_ is used as the basis for AI blue agent interaction with the PrimAITE environment
* `Networkx <https://github.com/networkx/networkx>`_ is used as the underlying data structure used for the PrimAITE environment
* `Stable Baselines 3 <https://github.com/DLR-RM/stable-baselines3>`_ is used as a default source of RL algorithms (although PrimAITE is not limited to SB3 agents)
* `Ray RLlib <https://github.com/ray-project/ray>`_ is used as an additional source of RL algorithms
* `Typer <https://github.com/tiangolo/typer>`_ is used for building CLIs (Command Line Interface applications)
* `Jupyterlab <https://github.com/jupyterlab/jupyterlab>`_ is used as an extensible environment for interactive and reproducible computing, based on the Jupyter Notebook Architecture
* `Platformdirs <https://github.com/platformdirs/platformdirs>`_ is used for finding the right location to store user data and configuration but varies per platform
* `Plotly <https://github.com/plotly/plotly.py>`_ is used for building high level charts


Where next?
------------

Head over to the :ref:`getting-started` page to install and setup PrimAITE!

.. toctree::
   :maxdepth: 8
   :caption: Contents:
   :hidden:

   source/getting_started
   source/about
   source/config
   source/primaite_session
   source/custom_agent
   source/simulation
   PrimAITE API <source/_autosummary/primaite>
   PrimAITE Tests <source/_autosummary/tests>
   source/dependencies
   source/glossary
   source/migration_1.2_-_2.0


.. TODO: Add project links once public repo has been created

.. toctree::
   :caption: Project Links:
   :hidden:

   Code <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE>
   Issues <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/issues>
   Pull Requests <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/pulls>
   Discussions <https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE/discussions>
