.. only:: comment

    © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK

Example Jupyter Notebooks
=========================

Executed Notebooks
------------------

There are a few example notebooks included which help with the understanding of PrimAITE's capabilities.

The PrimAITE documentation includes a pre executed example of notebooks. See :ref:`Executed Notebooks`.

In order to run the notebooks interactively, :ref:`install PrimAITE <getting-started>` and follow these steps:

Running Jupyter Notebooks
-------------------------

1. Navigate to the PrimAITE directory

.. code-block:: bash
    :caption: Unix

    cd ~/primaite/{VERSION}

.. code-block:: powershell
    :caption: Windows (Powershell)

    cd ~\primaite\{VERSION}

2. Run jupyter notebook (the python environment to which you installed PrimAITE must be active)

.. code-block:: bash
    :caption: Unix

    jupyter notebook

.. code-block:: powershell
    :caption: Windows (Powershell)

    jupyter notebook

3. Opening the jupyter webpage (optional)

The default web browser may automatically open the webpage. However, if that is not the case, click the link shown in your command prompt output. It should look like this: ``http://localhost:8888/?token=0123456798abc0123456789abc``


4. Navigate to the list of notebooks

The example notebooks are located in ``notebooks/example_notebooks/``. The file system shown in the jupyter webpage is relative to the location in which the ``jupyter notebook`` command was used.


Running Jupyter Notebooks via VSCode
------------------------------------

It is also possible to view the Jupyter notebooks within VSCode.

The best place to start is by opening a notebook file (.ipynb) in VSCode. If using VSCode to view a notebook for the first time, follow the steps below.

Installing extensions
"""""""""""""""""""""

VSCode may need some extensions to be installed if not already done.
To do this, press the "Select Kernel" button on the top right.

This should open a dialog which has the option to install python and jupyter extensions.

.. image:: ../../_static/notebooks/install_extensions.png
    :width: 700
    :align: center
    :alt: ::    The top dialog option that appears will automatically install the extensions

The following extensions should now be installed

.. image:: ../../_static/notebooks/extensions.png
    :width: 300
    :align: center

VSCode will then ask for a Python environment version to use. PrimAITE is compatible with Python versions 3.8 - 3.11

You should now be able to interact with the notebook.
