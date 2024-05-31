.. only:: comment

    © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK

Defining variations in the config files
================

PrimAITE supports the ability to use different variations on a scenario at different episodes. This can be used to increase domain randomisation to prevent overfitting, or to set up curriculum learning to train agents to perform more complicated tasks.

When using a fixed scenario, a single yaml config file is used. However, to use episode schedules, PrimAITE uses a directory with several config files that work together.
Defining variations in the config file.

Base scenario
*************

The base scenario is essentially the same as a fixed YAML configuration, but it can contain placeholders that are populated with episode-specific data at runtime. The base scenario contains any network, agent, or settings that remain fixed for the entire training/evaluation session.

The placeholders are defined as YAML Aliases and they are denoted by an asterisk (*placeholder).

Variations
**********

For each variation that could be used in a placeholder, there is a separate yaml file that contains the data that should populate the placeholder.

The data that fills the placeholder is defined as a YAML Anchor in a separate file, denoted by an ampersand ``&anchor``.

Learn more about YAML Aliases and Anchors here.

Schedule
********

Users must define which combination of scenario variations should be loaded in each episode. This takes the form of a YAML file with a relative path to the base scenario and a list of paths to be loaded in during each episode.

It takes the following format:

.. code-block:: yaml

    base_scenario: base.yaml
    schedule:
    0: # list of variations to load in at episode 0 (before the first call to env.reset() happens)
        - laydown_1.yaml
        - attack_1.yaml
    1: # list of variations to load in at episode 1 (after the first env.reset() call)
        - laydown_2.yaml
        - attack_2.yaml

For more information please refer to the ``Using Episode Schedules`` notebook in either :ref:`Executed Notebooks` or run the notebook interactively in ``notebooks/example_notebooks/``.

For further information around notebooks in general refer to the :ref:`Example Jupyter Notebooks`.
