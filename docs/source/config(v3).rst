Primaite v3 config
******************



The YAML file allows configuring a cybersecurity scenario involving a computer network and multiple agents. There are three main sections: training_config, game, and simulation.

The simulation section describes the simulated network environment with which the agetns interact.

The game section describes the agents and their capabilities. Each agent has a unique type and is associated with a team (GREEN, RED, or BLUE). Each agent has a configurable observation space, action space, and reward function.

The training_config section describes the training parameters for the learning agents. This includes the number of episodes, the number of steps per episode, and the number of steps before the agents start learning. The training_config section also describes the learning algorithm used by the agents. The learning algorithm is specified by the name of the algorithm and the hyperparameters for the algorithm. The hyperparameters are specific to each algorithm and are described in the documentation for each algorithm.

.. only:: comment
    This needs a bit of refactoring so I haven't written extensive documentation about the config yet.
