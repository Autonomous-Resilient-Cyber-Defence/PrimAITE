User Guide
===========

Getting Started
****************

**PrimAITE**

About The Project
PrimAITE (**PrimAITE**) simulation environment for training AI under the ARCD programme.It incorporates the functionality required
of a Primary-level environment, as specified in the Dstl ARCD Training Environment 

**PrimAITE** is currently under a closed development stage. 

**What's PrimAITE built with**

- OpenAI's Gym (https://gym.openai.com/)
- Networkx (https://github.com/networkx/networkx)
- Stable Baselines 3 (https://github.com/DLR-RM/stable-baselines3)
- Rllib (part of Ray) (https://github.com/ray-project/ray)


**Getting Started with PrimAITE**

Pre-Requisites

In order to get **PrimAITE** installed, you will need to have the following installed:

- `python3.8+`
- `python3-pip`
- `virtualenv`

**PrimAITE** is designed to be OS-agnostic, and thus should work on most variations/distros of Linux, Windows, and MacOS.

Installation from source
1. Navigate to the PrimAITE folder and create a new python virtual environment (venv)


``python3 -m venv <name_of_venv>``

2. Activate the venv

Unix

``source <name_of_venv>/bin/activate``

Windows

``.\<name_of_venv>\Scripts\activate``

3. Install `PrimAITE` into the venv along with all of it's dependencies
   
``python3 -m pip install -e .``

This will install all the dependencies including algorithm libraries. These libraries
all use ``torch``. If you'd like to install ``tensorflow`` for use with Rllib, you can do this manually
or install ``tensorflow`` as an optional dependency by postfixing the command in step 3 above with the ``[tensorflow]`` extra. Example:

To see all PrimAITE dependencies have a look at the dependencies page (:ref:`Dependencies`)

``python3 -m pip install -e .[tensorflow]``

Development Installation
To install the development dependencies, postfix the command in step 3 above with the ``[dev]`` extra. Example:

``python3 -m pip install -e .[dev]``



































