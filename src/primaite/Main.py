# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Primaite - main (harness) module

Coding Standards: PEP 8
"""

from sys import exc_info
import time
import yaml
import os.path
import logging
from datetime import datetime

from primaite.environment.primaite_env import Primaite
from primaite.transactions.transactions_to_file import write_transaction_to_file
from primaite.common.config_values_main import config_values_main

from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy as PPOMlp
from stable_baselines3 import A2C
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.evaluation import evaluate_policy

################################# FUNCTIONS ######################################

def run_generic():
    """
    Run against a generic agent
    """

    for episode in range(0, config_values.num_episodes):
        for step in range(0, config_values.num_steps):

            # Send the observation space to the agent to get an action
            # TEMP - random action for now
            # action = env.blue_agent_action(obs)
            action = env.action_space.sample()

            # Run the simulation step on the live environment
            obs, reward, done, info = env.step(action)

            # Break if done is True
            if done:
                break

            # Introduce a delay between steps
            time.sleep(config_values.time_delay / 1000)

        # Reset the environment at the end of the episode
        env.reset()

    env.close()


def run_stable_baselines3_ppo():
    """
    Run against a stable_baselines3 PPO agent
    """ 

    if config_values.load_agent == True:
        try:
            agent = PPO.load(config_values.agent_load_file, env, verbose=0, n_steps=config_values.num_steps)
        except:
            print("ERROR: Could not load agent at location: " + config_values.agent_load_file)
            logging.error("Could not load agent")
            logging.error("Exception occured", exc_info=True)
    else:
        agent = PPO(PPOMlp, env, verbose=0, n_steps=config_values.num_steps)

    if config_values.session_type == "TRAINING":
        # We're in a training session
        print("Starting training session...")
        logging.info("Starting training session...")
        for episode in range(0, config_values.num_episodes):
            agent.learn(total_timesteps=1)     
        save_agent(agent)
    else:
        # Default to being in an evaluation session
        print("Starting evaluation session...")
        logging.info("Starting evaluation session...")
        evaluate_policy(agent, env, n_eval_episodes=config_values.num_episodes)

    env.close()

def run_stable_baselines3_a2c():
    """
    Run against a stable_baselines3 A2C agent
    """

    if config_values.load_agent == True:
        try:
            agent = A2C.load(config_values.agent_load_file, env, verbose=0, n_steps=config_values.num_steps)
        except:
            print("ERROR: Could not load agent at location: " + config_values.agent_load_file)
            logging.error("Could not load agent")
            logging.error("Exception occured", exc_info=True)
    else:
        agent = A2C("MlpPolicy", env, verbose=0, n_steps=config_values.num_steps)

    if config_values.session_type == "TRAINING":
        # We're in a training session
        print("Starting training session...")
        logging.info("Starting training session...")
        for episode in range(0, config_values.num_episodes):
            agent.learn(total_timesteps=1)     
        save_agent(agent)
    else:
        # Default to being in an evaluation session
        print("Starting evaluation session...")
        logging.info("Starting evaluation session...")
        evaluate_policy(agent, env, n_eval_episodes=config_values.num_episodes)   

    env.close()

def save_agent(_agent):
    """
    Persist an agent (only works for stable baselines3 agents at present)
    """

    now = datetime.now() # current date and time
    time = now.strftime("%Y%m%d_%H%M%S")

    try:
        path = 'outputs/agents/'
        is_dir = os.path.isdir(path)
        if not is_dir:
            os.makedirs(path)
        filename = "outputs/agents/agent_saved_" + time
        _agent.save(filename)
        logging.info("Trained agent saved as " + filename)
    except Exception as e:
        logging.error("Could not save agent")
        logging.error("Exception occured", exc_info=True)

def configure_logging():
    """
    Configures logging
    """

    try:
        now = datetime.now() # current date and time
        time = now.strftime("%Y%m%d_%H%M%S")
        filename = "logs/app_" + time + ".log"
        path = 'logs/'
        is_dir = os.path.isdir(path)
        if not is_dir:
            os.makedirs(path)
        logging.basicConfig(filename=filename, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    except:
        print("ERROR: Could not start logging")

def load_config_values():
    """
    Loads the config values from the main config file into a config object
    """

    try:
        # Generic
        config_values.agent_identifier = config_data['agentIdentifier']           
        config_values.num_episodes = int(config_data['numEpisodes'])                                
        config_values.time_delay = int(config_data['timeDelay'])                  
        config_values.config_filename_use_case = config_data['configFilename']   
        config_values.session_type = config_data['sessionType']
        config_values.load_agent = bool(config_data['loadAgent'])
        config_values.agent_load_file = config_data['agentLoadFile']
        # Environment
        config_values.observation_space_high_value = int(config_data['observationSpaceHighValue'])
        # Reward values
        # Generic
        config_values.all_ok = int(config_data['allOk']) 
        # Node Operating State
        config_values.off_should_be_on = int(config_data['offShouldBeOn'])
        config_values.off_should_be_resetting = int(config_data['offShouldBeResetting'])
        config_values.on_should_be_off = int(config_data['onShouldBeOff'])
        config_values.on_should_be_resetting = int(config_data['onShouldBeResetting'])
        config_values.resetting_should_be_on = int(config_data['resettingShouldBeOn'])
        config_values.resetting_should_be_off = int(config_data['resettingShouldBeOff']) 
        config_values.resetting = int(config_data['resetting'])
        # Node O/S or Service State
        config_values.good_should_be_patching = int(config_data['goodShouldBePatching'])
        config_values.good_should_be_compromised = int(config_data['goodShouldBeCompromised'])
        config_values.good_should_be_overwhelmed = int(config_data['goodShouldBeOverwhelmed'])
        config_values.patching_should_be_good = int(config_data['patchingShouldBeGood'])
        config_values.patching_should_be_compromised = int(config_data['patchingShouldBeCompromised'])
        config_values.patching_should_be_overwhelmed = int(config_data['patchingShouldBeOverwhelmed'])
        config_values.patching = int(config_data['patching'])
        config_values.compromised_should_be_good = int(config_data['compromisedShouldBeGood'])
        config_values.compromised_should_be_patching = int(config_data['compromisedShouldBePatching'])
        config_values.compromised_should_be_overwhelmed = int(config_data['compromisedShouldBeOverwhelmed'])
        config_values.compromised = int(config_data['compromised'])     
        config_values.overwhelmed_should_be_good = int(config_data['overwhelmedShouldBeGood'])
        config_values.overwhelmed_should_be_patching = int(config_data['overwhelmedShouldBePatching'])
        config_values.overwhelmed_should_be_compromised = int(config_data['overwhelmedShouldBeCompromised'])
        config_values.overwhelmed = int(config_data['overwhelmed'])
        # Node File System State
        config_values.good_should_be_repairing = int(config_data['goodShouldBeRepairing'])
        config_values.good_should_be_restoring = int(config_data['goodShouldBeRestoring'])
        config_values.good_should_be_corrupt = int(config_data['goodShouldBeCorrupt'])
        config_values.good_should_be_destroyed = int(config_data['goodShouldBeDestroyed'])
        config_values.repairing_should_be_good = int(config_data['repairingShouldBeGood'])
        config_values.repairing_should_be_restoring = int(config_data['repairingShouldBeRestoring'])
        config_values.repairing_should_be_corrupt = int(config_data['repairingShouldBeCorrupt'])
        config_values.repairing_should_be_destroyed = int(config_data['repairingShouldBeDestroyed'])   
        config_values.repairing = int(config_data['repairing'])
        config_values.restoring_should_be_good = int(config_data['restoringShouldBeGood'])
        config_values.restoring_should_be_repairing = int(config_data['restoringShouldBeRepairing'])
        config_values.restoring_should_be_corrupt = int(config_data['restoringShouldBeCorrupt'])     
        config_values.restoring_should_be_destroyed = int(config_data['restoringShouldBeDestroyed'])
        config_values.restoring = int(config_data['restoring'])
        config_values.corrupt_should_be_good = int(config_data['corruptShouldBeGood'])
        config_values.corrupt_should_be_repairing = int(config_data['corruptShouldBeRepairing'])
        config_values.corrupt_should_be_restoring = int(config_data['corruptShouldBeRestoring'])
        config_values.corrupt_should_be_destroyed = int(config_data['corruptShouldBeDestroyed'])
        config_values.corrupt = int(config_data['corrupt'])
        config_values.destroyed_should_be_good = int(config_data['destroyedShouldBeGood'])
        config_values.destroyed_should_be_repairing = int(config_data['destroyedShouldBeRepairing'])
        config_values.destroyed_should_be_restoring = int(config_data['destroyedShouldBeRestoring'])
        config_values.destroyed_should_be_corrupt = int(config_data['destroyedShouldBeCorrupt'])
        config_values.destroyed = int(config_data['destroyed'])
        config_values.scanning = int(config_data['scanning'])
        # IER status
        config_values.red_ier_running = int(config_data['redIerRunning'])
        config_values.green_ier_blocked = int(config_data['greenIerBlocked'])
        # Patching / Reset durations
        config_values.os_patching_duration = int(config_data['osPatchingDuration'])                         
        config_values.node_reset_duration = int(config_data['nodeResetDuration'])                           
        config_values.service_patching_duration = int(config_data['servicePatchingDuration']) 
        config_values.file_system_repairing_limit = int(config_data['fileSystemRepairingLimit']) 
        config_values.file_system_restoring_limit = int(config_data['fileSystemRestoringLimit']) 
        config_values.file_system_scanning_limit = int(config_data['fileSystemScanningLimit']) 
        
        logging.info("Training agent: " + config_values.agent_identifier)
        logging.info("Training environment config: " + config_values.config_filename_use_case)
        logging.info("Training cycle has " + str(config_values.num_episodes) + " episodes")

    except Exception as e:
        logging.error("Could not save load config data")
        logging.error("Exception occured", exc_info=True)


################################# MAIN PROCESS ############################################

# Starting point

# Welcome message
print("Welcome to the Primary-level AI Training Environment (PrimAITE)")

# Configure logging
configure_logging()

# Open the main config file
try:
    config_file_main = open("config/config_main.yaml", "r")
    config_data = yaml.safe_load(config_file_main)
    # Create a config class
    config_values = config_values_main()
    # Load in config data
    load_config_values()
except Exception as e:
    logging.error("Could not load main config")
    logging.error("Exception occured", exc_info=True)

# Create a list of transactions
# A transaction is an object holding the: 
# - episode # 
# - step # 
# - initial observation space
# - action
# - reward
# - new observation space  
transaction_list = []

# Create the Primaite environment
try:
    env = Primaite(config_values, transaction_list)
    logging.info("PrimAITE environment created")
except Exception as e:
    logging.error("Could not create PrimAITE environment")
    logging.error("Exception occured", exc_info=True)

# Get the number of steps (which is stored in the child config file)
config_values.num_steps = env.episode_steps

# Run environment against an agent
if config_values.agent_identifier == "GENERIC":
    run_generic()
elif config_values.agent_identifier == "STABLE_BASELINES3_PPO":
    run_stable_baselines3_ppo()
elif config_values.agent_identifier == "STABLE_BASELINES3_A2C":
    run_stable_baselines3_a2c()

print("Session finished")
logging.info("Session finished")

print("Saving transaction logs...")
logging.info("Saving transaction logs...")

write_transaction_to_file(transaction_list)

config_file_main.close

print("Finished")
logging.info("Finished")








