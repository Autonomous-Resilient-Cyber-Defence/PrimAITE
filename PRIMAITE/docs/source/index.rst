.. PrimAITE documentation master file, created by
   sphinx-quickstart on Thu Dec  8 09:51:18 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PrimAITE's documentation
====================================

What is PrimAITE?
------------------------

PrimAITE (Primary-level AI Training Environment) is a simulation environment for training AI under the ARCD programme​. It incorporates the functionality required of a Primary-level environment, as specified in the Dstl ARCD Training Environment Matrix document:​

* The ability to model a relevant platform / system context; 
* The ability to model key characteristics of a platform / system by representing connections, IP addresses, ports, traffic loading, operating systems, services and processes; 
* Operates at machine-speed to enable fast training cycles. 

PrimAITE aims to evolve into an ARCD environment that could be used as the follow-on from Reception level approaches (e.g. YAWNING TITAN), and help bridge the Sim-to-Real gap into Secondary level environments (e.g. IMAGINARY YAK)​.

This is similar to the approach taken by FVEY international partners (e.g. AUS CyBORG, US NSA FARLAND and CAN CyGil). These environments are referenced by the Dstl ARCD Agent Training Environments Knowledge Transfer document (TR141342)​.

What is PrimAITE built with
--------------------------------------

* `OpenAI's Gym <https://gym.openai.com/>`_ is used as the basis for AI blue agent interaction with the PrimAITE environment
* `Networkx <https://github.com/networkx/networkx>`_ is used as the underlying data structure used for the PrimAITE environment
* `Stable Baselines 3 <https://github.com/DLR-RM/stable-baselines3>`_ is used as a default source of RL algorithms (although PrimAITE is not limited to SB3 agents)

Where next?
------------

The best place to start is :ref:`about`

.. toctree::
   :maxdepth: 8
   :caption: Contents:

   about
   dependencies
   config
   training
   results
