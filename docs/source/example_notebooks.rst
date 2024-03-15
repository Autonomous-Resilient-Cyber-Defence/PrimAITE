.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Example Jupyter Notebooks
=========================

There are a few example notebooks included which help with the understanding of PrimAITE's capabilities.

The Jupyter Notebooks can be run via the 2 examples below. These assume that the instructions to install PrimAITE from the :ref:`Getting Started <getting-started>` page is completed as a prerequisite.

Running Jupyter Notebooks
-------------------------

1. Navigate to the PrimAITE directory

.. code-block:: bash
    :caption: Unix

    cd ~/primaite/{VERSION}

.. code-block:: powershell
    :caption: Windows (Powershell)

    cd ~\primaite\{VERSION}

2. Run jupyter notebook

.. code-block:: bash
    :caption: Unix

    jupyter notebook

.. code-block:: powershell
    :caption: Windows (Powershell)

    jupyter notebook

3. Opening the jupyter webpage (optional)

The default web browser may automatically open the webpage. However, if that is not the case, open a web browser and navigate to |jupyter_index|.

.. |jupyter_index| raw:: html

   <a href="http://localhost:8888/tree" target="_blank">http://localhost:8888/tree</a>

4. Navigate to the list of notebooks

The example notebooks are located in notebooks/example_notebooks or by navigating to |jupyter_index_notebooks|

.. |jupyter_index_notebooks| raw:: html

   <a href="http://localhost:8888/tree/notebooks/example_notebooks" target="_blank">http://localhost:8888/tree/notebooks/example_notebooks</a>

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

VSCode will then ask for a Python environment version to use. PrimAITE is compatible with Python versions 3.8 - 3.10

You should now be able to interact with the notebook.
