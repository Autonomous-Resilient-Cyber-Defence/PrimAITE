.. only:: comment

    Crown Owned Copyright (C) Dstl 2023. DEFCON 703. Shared in confidence.

.. _getting-started:

Getting Started
===============

**Getting Started with PrimAITE**

Pre-Requisites

In order to get **PrimAITE** installed, you will need to have a python version between 3.8 and 3.10 installed. If you don't already have it, this is how to install it:


.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        sudo add-apt-repository ppa:deadsnakes/ppa
        sudo apt install python3.10
        sudo apt-get install python3-pip
        sudo apt-get install python3-venv

    .. code-tab:: text
        :caption: Windows (Powershell)

        - Manual install from: https://www.python.org/downloads/release/python-31011/

**PrimAITE** is designed to be OS-agnostic, and thus should work on most variations/distros of Linux, Windows, and MacOS.

Install PrimAITE
****************

1. Create a primaite directory in your home directory:

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        mkdir ~/primaite

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        mkdir ~\primaite

2. Navigate to the primaite directory and create a new python virtual environment (venv)

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        cd ~/primaite
        python3 -m venv .venv

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        cd ~\primaite
        python3 -m venv .venv
        attrib +h .venv /s /d # Hides the .venv directory

3. Activate the venv

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        source .venv/bin/activate

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        .\.venv\Scripts\activate


4. Install PrimAITE using pip from PyPi

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        pip install primaite

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        pip install primaite

5. Perform the PrimAITE setup

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        primaite setup

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        primaite setup

Clone & Install PrimAITE for Development
****************************************

To be able to extend PrimAITE further, or to build wheels manually before install, clone the repository to a location
of your choice:

.. TODO:: Add repo path once we know what it is

.. code-block:: bash

    git clone <repo path>
    cd primaite

Create and activate your Python virtual environment (venv)

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        python3 -m venv venv
        source venv/bin/activate

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        python3 -m venv venv
        .\venv\Scripts\activate

Install PrimAITE with the dev extra

.. tabs:: lang

    .. code-tab:: bash
        :caption: Unix

        pip install -e .[dev]

    .. code-tab:: powershell
        :caption: Windows (Powershell)

        pip install -e .[dev]


To view the complete list of packages installed during PrimAITE installation, go to the dependencies page (:ref:`Dependencies`).
