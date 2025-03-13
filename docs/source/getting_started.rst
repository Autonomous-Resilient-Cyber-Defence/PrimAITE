.. only:: comment

    © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK

.. _getting-started:

Getting Started
===============

**Getting Started with PrimAITE**

Pre-Requisites

In order to get **PrimAITE** installed, you will need Python, venv, and pip. If you don't already have them, this is how to install it:


.. code-block:: bash
    :caption: Unix

    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt install python3.10
    sudo apt-get install python3-pip
    sudo apt-get install python3-venv


.. code-block:: text
    :caption: Windows (Powershell)

    - Manual install from: https://www.python.org/downloads/release/python-31011/

**PrimAITE** is designed to be OS-agnostic, and thus should work on most variations/distros of Linux, Windows, and MacOS.

Installing PrimAITE has been tested with all supported python versions, venv 20.24.1, and pip 23.

Install PrimAITE
****************

1. Create a directory for your PrimAITE project:

.. code-block:: bash
    :caption: Unix

    mkdir -p ~/primaite/{VERSION}

.. code-block:: powershell
    :caption: Windows (Powershell)

    mkdir ~\primaite\{VERSION}


2. Navigate to the primaite directory and create a new python virtual environment (venv)

.. code-block:: bash
    :caption: Unix

    cd ~/primaite/{VERSION}
    python3 -m venv .venv

.. code-block:: powershell
    :caption: Windows (Powershell)

        cd ~\primaite\{VERSION}
        python3 -m venv .venv
        attrib +h .venv /s /d # Hides the .venv directory


3. Activate the venv

.. code-block:: bash
    :caption: Unix

    source .venv/bin/activate

.. code-block:: powershell
    :caption: Windows (Powershell)

    .\.venv\Scripts\activate


4. Install PrimAITE from your saved wheel file

.. code-block:: bash
    :caption: Unix

    pip install path/to/your/primaite.whl[rl]

.. code-block:: powershell
    :caption: Windows (Powershell)

    pip install path\to\your\primaite.whl

5. Perform the PrimAITE setup

.. code-block:: bash
    :caption: Unix

    primaite setup

.. code-block:: powershell
    :caption: Windows (Powershell)

        primaite setup

Clone & Install PrimAITE for Development
****************************************

To be able to extend PrimAITE further, or to build wheels manually before install, clone the repository to a location
of your choice:

1. Clone the repository.

For example:

.. code-block:: bash

    git clone https://github.com/Autonomous-Resilient-Cyber-Defence/PrimAITE
    cd primaite

2. Create and activate your Python virtual environment (venv)

.. code-block:: bash
    :caption: Unix

    python3 -m venv venv
    source venv/bin/activate

.. code-block:: powershell
    :caption: Windows (Powershell)

    python3 -m venv venv
    .\venv\Scripts\activate

3. Install PrimAITE with the dev extra

.. code-block:: bash
    :caption: Unix

    pip install -e .[dev,rl]

.. code-block:: powershell
    :caption: Windows (Powershell)

    pip install -e .[dev,rl]

To view the complete list of packages installed during PrimAITE installation, go to the dependencies page (:ref:`Dependencies`).

4. Set PrimAITE to run on development mode

Running step 3 should have installed PrimAITE, verify this by running

.. code-block:: bash
    :caption: Unix

    primaite setup

.. code-block:: powershell
    :caption: Windows (Powershell)

    primaite setup

To set PrimAITE to run in development mode:

.. code-block:: bash
    :caption: Unix

    primaite dev-mode enable

.. code-block:: powershell
    :caption: Windows (Powershell)

    primaite dev-mode enable

More information about :ref:`Developer Tools`
