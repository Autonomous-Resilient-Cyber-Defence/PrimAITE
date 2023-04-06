.. _results:

Results, Output and Logging from PrimAITE
=========================================

PrimAITE produces four types of data:

* Outputs - Results
* Outputs - Diagrams
* Outputs - Saved agents
* Logging

Outputs can be found in the *[Install Directory]\\PRIMAITE\\PRIMAITE\\outputs* directory

Logging can be found in the *[Install Directory]\\PRIMAITE\\PRIMAITE\\logs* directory

**Outputs - Results**

PrimAITE automatically creates two sets of results from each session, and stores them in the *Results* folder:

* Average reward per episode - a csv file listing the average reward for each episode of the session. This provides, for example, an indication of the change over a training session of the reward value
* All transactions - a csv file listing the following values for every step of every episode:

	* Timestamp
	* Episode number
	* Step number
	* Initial observation space (before red and blue agent actions have been taken). Individual elements of the observation space are presented in the format OSI_X_Y
	* Resulting observation space (after the red and blue agent actions have been taken) Individual elements of the observation space are presented in the format OSN_X_Y
	* Reward value
	* Action space (as presented by the blue agent on this step). Individual elements of the action space are presented in the format AS_X

**Outputs - Diagrams**

For each session, PrimAITE automatically creates a visualisation of the system / network laydown configuration, and stores it in the *Diagrams* folder.

**Outputs - Saved agents**

For each training session, assuming the agent being trained implements the *save()* function and this function is called by the code, PrimAITE automatically saves the agent state and stores it in the *agents* folder.

**Logging**

PrimAITE also provides output logs (for diagnosis) using the Python Logging package. These can be found in the *[Install Directory]\\PRIMAITE\\PRIMAITE\\logs* directory