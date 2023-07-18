.. only:: comment

    Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.

v1.2 to v2.0 Migration guide
============================

**1. Installing PrimAITE**

    Like before, you can install primaite from the repository by running ``pip install -e .``. But, there is now an additional setup step which does several things, like setting up user directories, copy default configs and notebooks, etc. Once you have installed PrimAITE to your virtual environment, run this command to finalise setup.

    .. code-block:: bash

        primaite setup

**2. Running a training session**

    In version 1.2 of PrimAITE, the main entry point for training or evaluating agents was the ``src/primaite/main.py`` file. v2.0.0 introduced managed 'sessions' which are responsible for reading configuration files, performing training, and writing outputs.

    ``main.py`` file still runs a training session but it now uses the new `PrimaiteSession`, and it now requires you to provide the path to your config files.

    .. code-block:: bash

        python src/primaite/main.py --tc path/to/training-config.yaml --ldc path/to/laydown-config.yaml

    Alternatively, the session can be invoked via the commandline by running:

    .. code-block:: bash

        primaite session --tc path/to/training-config.yaml --ldc path/to/laydown-config.yaml

**3. Location of configs**

    In version 1.2, training configs and laydown configs were all stored in the project repository under ``src/primaite/config``. Version 2.0.0 introduced user data directories, and now when you install and setup PrimAITE, config files are stored in your user data location. On Linux/OSX, this is stored in ``~/primaite/config``. On Windows, this is stored in ``C:\Users\<your username>\primaite\configs``. Upon first setup, the configs folder is populated with some default yaml files. It is recommended that you store all your custom configuration files here.

**4. Contents of configs**

    Some things that were previously part of the laydown config are now part of the traning config.

        * Actions

    If you have custom configs which use these, you will need to adapt them by moving the configuration from the laydown config to the training config.

    Also, there are new configurable items in the training config:

        * Observations
        * Agent framework
        * Agent
        * Deep learning framework
        * random red agents
        * seed
        * deterministic
        * hard coded agent view

    Each of these items have default values which are designed so that PrimAITE has the same behaviour as it did in 1.2.0, so you do not have to specify them.

    ACL Rules in laydown configs have a new required parameter: ``position``. The lower the position, the higher up in the ACL table the rule will placed. If you have custom laydowns, you will need to go through them and add a position to each ACL_RULE.
