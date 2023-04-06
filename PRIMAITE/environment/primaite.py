# Crown Copyright (C) Dstl 2022. DEFCON 703. Shared in confidence.
"""
Main environment module containing the PRIMmary AI Training Evironment (PRIMAITE) class
"""

import numpy as np
import networkx as nx
import copy
import csv
import yaml
import os.path
import logging

from gym import Env, spaces
from matplotlib import pyplot as plt
from datetime import datetime

from common.enums import *
from links.link import Link
from pol.ier import IER
from nodes.node_state_instruction_green import NodeStateInstructionGreen
from nodes.node_state_instruction_red import NodeStateInstructionRed
from pol.green_pol import apply_iers, apply_node_pol
from pol.red_agent_pol import apply_red_agent_iers, apply_red_agent_node_pol
from nodes.active_node import ActiveNode
from nodes.passive_node import PassiveNode
from nodes.service_node import ServiceNode
from common.service import Service
from acl.access_control_list import AccessControlList
from environment.reward import calculate_reward_function
from transactions.transaction import Transaction

class PRIMAITE(Env):
    """
    PRIMmary AI Training Evironment (PRIMAITE) class
    """

    # Observation / Action Space contants
    OBSERVATION_SPACE_FIXED_PARAMETERS = 4
    ACTION_SPACE_NODE_PROPERTY_VALUES = 5
    ACTION_SPACE_NODE_ACTION_VALUES = 4
    ACTION_SPACE_ACL_ACTION_VALUES = 3
    ACTION_SPACE_ACL_PERMISSION_VALUES = 2

    OBSERVATION_SPACE_HIGH_VALUE = 1000000      # Highest value within an observation space

    def __init__(self, _config_values, _transaction_list):
        """
        Init

        Args:
            _episode_steps: The number of steps for the episode
            _config_filename: The name of config file
            _transaction_list: The list of transactions to populate
            _agent_identifier: Identifier for the agent
        """

        super(PRIMAITE, self).__init__()

        # Take a copy of the config values
        self.config_values = _config_values

        # Number of steps in an episode
        self.episode_steps = 0

        # Transaction list
        self.transaction_list = _transaction_list

        # The agent in use
        self.agent_identifier = self.config_values.agent_identifier

        # Create a dictionary to hold all the nodes
        self.nodes = {}

        # Create a dictionary to hold a reference set of nodes
        self.nodes_reference = {}

        # Create a dictionary to hold all the links
        self.links = {}

        # Create a dictionary to hold a reference set of links
        self.links_reference = {}

        # Create a dictionary to hold all the green IERs (this will come from an external source)
        self.green_iers = {}

        # Create a dictionary to hold all the node PoLs (this will come from an external source)
        self.node_pol = {}

        # Create a dictionary to hold all the red agent IERs (this will come from an external source)
        self.red_iers = {}

        # Create a dictionary to hold all the red agent node PoLs (this will come from an external source)
        self.red_node_pol = {}

        # Create the Access Control List
        self.acl = AccessControlList()

        # Create a list of services (enums)
        self.services_list = []

        # Create a list of ports
        self.ports_list = []

        # Create graph (network)
        self.network = nx.MultiGraph()

        # Create a graph (network) reference
        self.network_reference = nx.MultiGraph()

        # Create step count
        self.step_count = 0

        # Create step info dictionary
        self.step_info = {}

        # Total reward
        self.total_reward = 0

        # Average reward
        self.average_reward = 0

        # Episode count
        self.episode_count = 0

        # Number of nodes - gets a value by examining the nodes dictionary after it's been populated
        self.num_nodes = 0

        # Number of links - gets a value by examining the links dictionary after it's been populated
        self.num_links = 0

        # Number of services - gets a value when config is loaded
        self.num_services = 0

        # Number of ports - gets a value when config is loaded
        self.num_ports = 0

        # The action type
        self.action_type = 0

        # Open the config file and build the environment laydown
        try:
            self.config_file = open("config/" + self.config_values.config_filename_use_case, "r")
            self.config_data = yaml.safe_load(self.config_file)
            self.load_config()
        except Exception as e:
            logging.error("Could not load the environment configuration")
            logging.error("Exception occured", exc_info=True)

        # Store the node objects as node attributes
        # (This is so we can access them as objects)
        for node in self.network:
            self.network.nodes[node]["self"] = node

        for node in self.network_reference:
            self.network_reference.nodes[node]["self"] = node

        self.num_nodes = len(self.nodes)
        self.num_links = len(self.links)

        # Visualise in PNG
        try:
            plt.tight_layout()
            nx.draw_networkx(self.network, with_labels=True)
            now = datetime.now() # current date and time
            time = now.strftime("%Y%m%d_%H%M%S")

            path = 'outputs/diagrams'
            is_dir = os.path.isdir(path)
            if not is_dir:
                os.makedirs(path)
            filename = "outputs/diagrams/network_" + time + ".png"
            plt.savefig(filename, format="PNG")
            plt.clf()
        except Exception as a:
            logging.error("Could not save network diagram")
            logging.error("Exception occured", exc_info=True)
            print("Could not save network diagram")

        # Define Observation Space
        # x = number of nodes and links (i.e. items)
        # y = number of parameters to be sent
        # For each item, we send:
        # - [For Nodes]              |      [For Links]
        # - node ID                  |      link ID
        # - operating state          |      N/A
        # - operating system state   |      N/A
        # - file system state        |      N/A
        # - service A state          |      service A loading
        # - service B state          |      service B loading
        # - service C state          |      service C loading
        # - service D state          |      service D loading
        # - service E state          |      service E loading
        # - service F state          |      service F loading
        # - service G state          |      service G loading

        # Calculate the number of items that need to be included in the observation space
        num_items = self.num_links + self.num_nodes
        # Set the number of observation parameters, being # of services plus id, operating state, file system state and O/S state (i.e. 4)
        self.num_observation_parameters = self.num_services + self.OBSERVATION_SPACE_FIXED_PARAMETERS
        # Define the observation shape
        self.observation_shape = (num_items, self.num_observation_parameters)
        self.observation_space = spaces.Box(low=0, 
                                            high=self.config_values.observation_space_high_value,
                                            shape=self.observation_shape,
                                            dtype=np.int64)

        # This is the observation that is sent back via the rest and step functions
        self.env_obs = np.zeros(self.observation_shape, dtype=np.int64)

        # Define Action Space - depends on action space type (Node or ACL)
        if self.action_type == ACTION_TYPE.NODE:
            logging.info("Action space type NODE selected")
            # Terms (for node action space):
            # [0, num nodes] - node ID (0 = nothing, node ID)
            # [0, 4] - what property it's acting on (0 = nothing, state, o/s state, service state, file system state)
            # [0, 3] - action on property (0 = nothing, On / Scan, Off / Repair, Reset / Patch / Restore)
            # [0, num services] - resolves to service ID (0 = nothing, resolves to service)
            self.action_space = spaces.MultiDiscrete([self.num_nodes, self.ACTION_SPACE_NODE_PROPERTY_VALUES, self.ACTION_SPACE_NODE_ACTION_VALUES, self.num_services])
        else:
            logging.info("Action space type ACL selected")
            # Terms (for ACL action space):
            # [0, 2] - Action (0 = do nothing, 1 = create rule, 2 = delete rule)
            # [0, 1] - Permission (0 = DENY, 1 = ALLOW)
            # [0, num nodes] - Source IP (0 = any, then 1 -> x resolving to IP addresses)
            # [0, num nodes] - Dest IP (0 = any, then 1 -> x resolving to IP addresses)
            # [0, num services] - Protocol (0 = any, then 1 -> x resolving to protocol)
            # [0, num ports] - Port (0 = any, then 1 -> x resolving to port)
            self.action_space = spaces.MultiDiscrete([self.ACTION_SPACE_ACL_ACTION_VALUES, self.ACTION_SPACE_ACL_PERMISSION_VALUES, self.num_nodes + 1, self.num_nodes + 1, self.num_services + 1, self.num_ports + 1])
            
        # Set up a csv to store the results of the training
        try:
            now = datetime.now() # current date and time
            time = now.strftime("%Y%m%d_%H%M%S")
            header = ['Episode', 'Average Reward']

            # Check whether the output/rerults folder exists (doesn't exist by default install)
            path = 'outputs/results/'
            is_dir = os.path.isdir(path)
            if not is_dir:
                os.makedirs(path)
            filename = "outputs/results/average_reward_per_episode_" + time + ".csv"
            self.csv_file = open(filename, 'w', encoding='UTF8', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow(header)
        except Exception as e:
            logging.error("Could not create csv file to hold average reward per episode")
            logging.error("Exception occured", exc_info=True)

    def reset(self):
        """
        AI Gym Reset function

        Returns:
             Environment observation space (reset)
        """

        csv_data = self.episode_count, self.average_reward
        self.csv_writer.writerow(csv_data)

        self.episode_count += 1
        
        # Don't need to reset links, as they are cleared and recalculated every step
        
        # Clear the ACL
        self.init_acl()

        # Reset the node statuses and recreate the ACL from config
        # Does this for both live and reference nodes
        self.reset_environment()

        # Reset counters and totals
        self.total_reward = 0
        self.step_count = 0
        self.average_reward = 0

        # Update observations space and return
        self.update_environent_obs()
        return self.env_obs

    def step(self, action):
        """
        AI Gym Step function

        Args:
            action: Action space from agent

        Returns:
             env_obs: Observation space
             reward: Reward value for this step
             done: Indicates episode is complete if True
             step_info: Additional information relating to this step
        """

        if self.step_count == 0:
            print("Episode: " + str(self.episode_count) + " running")

        # TEMP
        done = False

        self.step_count += 1
        #print("Episode step: " + str(self.stepCount))           
          
        # Need to clear traffic on all links first
        for link_key, link_value in self.links.items():
            link_value.clear_traffic()

        # Create a Transaction (metric) object for this step
        transaction = Transaction(datetime.now(), self.agent_identifier, self.episode_count, self.step_count)
        # Load the initial observation space into the transaction
        transaction.set_obs_space_pre(copy.deepcopy(self.env_obs))
        # Load the action space into the transaction
        transaction.set_action_space(copy.deepcopy(action))

        # 1. Perform any time-based activities (e.g. a component moving from patching to good)
        self.apply_time_based_updates()

        # 2. Apply PoL
        apply_node_pol(self.nodes, self.node_pol, self.step_count)                                          # Node PoL
        apply_iers(self.network, self.nodes, self.links, self.green_iers, self.acl, self.step_count)        # Network PoL  
        # Take snapshots of nodes and links
        self.nodes_post_pol = copy.deepcopy(self.nodes)
        self.links_post_pol = copy.deepcopy(self.links) 
        # Reference
        apply_node_pol(self.nodes_reference, self.node_pol, self.step_count)                                                            # Node PoL
        apply_iers(self.network_reference, self.nodes_reference, self.links_reference, self.green_iers, self.acl, self.step_count)      # Network PoL  

        # 3. Implement Red Action      
        apply_red_agent_iers(self.network, self.nodes, self.links, self.red_iers, self.acl, self.step_count)
        apply_red_agent_node_pol(self.nodes, self.red_iers, self.red_node_pol, self.step_count)
        # Take snapshots of nodes and links
        self.nodes_post_red = copy.deepcopy(self.nodes)
        self.links_post_red = copy.deepcopy(self.links)  

        # 4. Implement Blue Action
        self.interpret_action_and_apply(action)

        # 5. Reapply normal and Red agent IER PoL, as we need to see what effect the blue agent action has had (if any) on link status
        # Need to clear traffic on all links first
        for link_key, link_value in self.links.items():
            link_value.clear_traffic()
        apply_iers(self.network, self.nodes, self.links, self.green_iers, self.acl, self.step_count)
        apply_red_agent_iers(self.network, self.nodes, self.links, self.red_iers, self.acl, self.step_count)
        # Take snapshots of nodes and links
        self.nodes_post_blue = copy.deepcopy(self.nodes)
        self.links_post_blue = copy.deepcopy(self.links) 

        # 6. Calculate reward signal (for RL)
        reward = calculate_reward_function(self.nodes_post_pol, self.nodes_post_blue, self.nodes_reference, self.green_iers, self.red_iers, self.step_count, self.config_values)
        #print("Step reward: " + str(reward))  
        self.total_reward += reward
        if self.step_count == self.episode_steps:
            self.average_reward = self.total_reward / self.step_count
            if self.config_values.session_type == "EVALUATION":
                # For evaluation, need to trigger the done value = True when step count is reached in order to prevent neverending episode
                done = True
            print("Average reward: " + str(self.average_reward)) 
        # Load the reward into the transaction
        transaction.set_reward(reward)
        
        # 7. Output Verbose
        #self.output_link_status()

        # 8. Update env_obs
        self.update_environent_obs()
        # Load the new observation space into the transaction
        transaction.set_obs_space_post(copy.deepcopy(self.env_obs))

        # 9. Add the transaction to the list of transactions
        self.transaction_list.append(copy.deepcopy(transaction))

        # Return
        return self.env_obs, reward, done, self.step_info

    def __close__(self):
        """
        Override close function
        """

        self.csv_file.close()
        self.config_file.close()

    def init_acl(self):
        """
        Initialise the Access Control List
        """

        self.acl.remove_all_rules()     
    
    def output_link_status(self):
        """
        Output the link status of all links to the console
        """

        for link_key, link_value in self.links.items():
            print("Link ID: " + link_value.get_id())
            for protocol in link_value.get_protocol_list():
                print("    Protocol: " + protocol.get_name().name + ", Load: " + str(protocol.get_load()))

    def interpret_action_and_apply(self, _action):
        """
        Applies agent actions to the nodes and Access Control List

        Args:
            _action: The action space from the agent
        """

        # At the moment, actions are only affecting nodes
        if self.action_type == ACTION_TYPE.NODE:
            self.apply_actions_to_nodes(_action)
        else:
            self.apply_actions_to_acl(_action)

    def apply_actions_to_nodes(self, _action):
        """
        Applies agent actions to the nodes

        Args:
            _action: The action space from the agent
        """

        node_id = _action[0]
        node_property = _action[1]
        property_action = _action[2]
        service_index = _action[3]

        # Check that the action is requesting a valid node
        try:
            node = self.nodes[str(node_id)]
        except:
            return

        if node_property == 0:
            # This is the do nothing action
            return
        elif node_property == 1:
            # This is an action on the node Operating State
            if property_action == 0:
                # Do nothing
                return
            elif property_action == 1:
                # Turn on (only applicable if it's OFF, not if it's patching)
                if node.get_state() == HARDWARE_STATE.OFF:
                    node.turn_on()
            elif property_action == 2:
                # Turn off
                node.turn_off()
            elif property_action == 3:
                # Reset (only applicable if it's ON)
                if node.get_state() == HARDWARE_STATE.ON:
                    node.reset()
            else:
                return
        elif node_property == 2:
            if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                # This is an action on the node Operating System State
                if property_action == 0:
                    # Do nothing
                    return
                elif property_action == 1:
                    # Patch (valid action if it's good or compromised)
                    node.set_os_state(SOFTWARE_STATE.PATCHING)
            else:
                # Node is not of Active or Service Type
                return
        elif node_property == 3:
            # This is an action on a node Service State
            if isinstance(node, ServiceNode):
                # This is an action on a node Service State
                if property_action == 0:
                    # Do nothing
                    return
                elif property_action == 1:
                    # Patch (valid action if it's good or compromised)
                    node.set_service_state(self.services_list[service_index], SOFTWARE_STATE.PATCHING)
            else:
                # Node is not of Service Type
                return
        elif node_property == 4:
            # This is an action on a node file system state
            if isinstance(node, ActiveNode):
                if property_action == 0:
                    # Do nothing
                    return
                elif property_action == 1:
                    # Scan
                    node.start_file_system_scan()
                elif property_action == 2:
                    # Repair
                    # You cannot repair a destroyed file system - it needs restoring
                    if node.get_file_system_state_actual() != FILE_SYSTEM_STATE.DESTROYED:
                        node.set_file_system_state(FILE_SYSTEM_STATE.REPAIRING)
                elif property_action == 3:
                    # Restore
                    node.set_file_system_state(FILE_SYSTEM_STATE.RESTORING)
            else:
                # Node is not of Active Type
                return
        else:
            return

    def apply_actions_to_acl(self, _action):
        """
        Applies agent actions to the Access Control List [TO DO]

        Args:
            _action: The action space from the agent
        """

        action_decision = _action[0]
        action_permission = _action[1]
        action_source_ip = _action[2]
        action_destination_ip = _action[3]
        action_protocol = _action[4]
        action_port = _action[5]

        if action_decision == 0:
            # It's decided to do nothing
            return
        else:  
            # It's decided to create a new ACL rule or remove an existing rule
            # Permission value
            if action_permission == 0:
                acl_rule_permission = "DENY"
            else:
                acl_rule_permission = "ALLOW"
            # Source IP value
            if action_source_ip == 0:
                acl_rule_source = "ANY"
            else:
                node = list(self.nodes.values())[action_source_ip - 1]
                if isinstance(node, ServiceNode) or isinstance(node, ActiveNode):
                    acl_rule_source = node.get_ip_address()
                else:
                    return
            # Destination IP value
            if action_destination_ip == 0:
                acl_rule_destination = "ANY"
            else:
                node = list(self.nodes.values())[action_destination_ip - 1]
                if isinstance(node, ServiceNode) or isinstance(node, ActiveNode):
                    acl_rule_destination = node.get_ip_address()
                else:
                    return
            # Protocol value
            if action_protocol == 0:
                acl_rule_protocol = "ANY"
            else:
                acl_rule_protocol = self.services_list[action_protocol - 1]
            # Port value
            if action_port == 0:
                acl_rule_port = "ANY"
            else:
                acl_rule_port = self.ports_list[action_port - 1]

            # Now add or remove
            if action_decision == 1:
                # Add the rule
                self.acl.add_rule(acl_rule_permission, acl_rule_source, acl_rule_destination, acl_rule_protocol, acl_rule_port)
            elif action_decision == 2:
                # Remove the rule
                self.acl.remove_rule(acl_rule_permission, acl_rule_source, acl_rule_destination, acl_rule_protocol, acl_rule_port)
            else:
                return

    def apply_time_based_updates(self):
        """
        Updates anything that needs to count down and then change state (e.g. reset / patching status)
        """
        
        for node_key, node in self.nodes.items():
            if node.get_state() == HARDWARE_STATE.RESETTING:
                node.update_resetting_status()
            else:
                pass
            if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                node.update_file_system_state()
                if node.get_os_state() == SOFTWARE_STATE.PATCHING:
                    node.update_os_patching_status()
                else:
                    pass
            else:
                pass
            if isinstance(node, ServiceNode):
                node.update_services_patching_status()
            else:
                pass

        for node_key, node in self.nodes_reference.items():
            if node.get_state() == HARDWARE_STATE.RESETTING:
                node.update_resetting_status()
            else:
                pass
            if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                node.update_file_system_state()
                if node.get_os_state() == SOFTWARE_STATE.PATCHING:
                    node.update_os_patching_status()
                else:
                    pass
            else:
                pass
            if isinstance(node, ServiceNode):
                node.update_services_patching_status()
            else:
                pass

    def update_environent_obs(self):
        """
        # Updates the observation space based on the node and link status
        """  
        
        item_index = 0

        # Do nodes first
        for node_key, node in self.nodes.items():
            self.env_obs[item_index][0] = int(node.get_id())
            self.env_obs[item_index][1] = node.get_state().value
            if isinstance(node, ActiveNode) or isinstance(node, ServiceNode):
                self.env_obs[item_index][2] = node.get_os_state().value
                self.env_obs[item_index][3] = node.get_file_system_state_observed().value
            else:
                self.env_obs[item_index][2] = 0
                self.env_obs[item_index][3] = 0                
            service_index = 4
            if isinstance(node, ServiceNode):              
                for service in self.services_list:
                    if node.has_service(service):
                        self.env_obs[item_index][service_index] = node.get_service_state(service).value
                    else:
                        self.env_obs[item_index][service_index] = 0
                    service_index += 1
            else:
                # Not a service node
                for service in self.services_list:
                    self.env_obs[item_index][service_index] = 0
                    service_index += 1
            item_index += 1

        # Now do links
        for link_key, link in self.links.items():
            self.env_obs[item_index][0] = int(link.get_id())
            self.env_obs[item_index][1] = 0
            self.env_obs[item_index][2] = 0
            self.env_obs[item_index][3] = 0
            protocol_list = link.get_protocol_list()
            protocol_index = 0
            for protocol in protocol_list:
                self.env_obs[item_index][protocol_index + 4] = protocol.get_load()
                protocol_index += 1
            item_index += 1

    def load_config(self):
        """
        # Loads config data in order to build the environment configuration
        """ 

        for item in self.config_data:
            if item["itemType"] == "NODE":
                # Create a node
                self.create_node(item)
            elif item["itemType"] == "LINK":
                # Create a link
                self.create_link(item)              
            elif item["itemType"] == "GREEN_IER":
                # Create a Green IER
                self.create_green_ier(item)
            elif item["itemType"] == "GREEN_POL":
                # Create a Green PoL
                self.create_green_pol(item)
            elif item["itemType"] == "RED_IER":
                # Create a Red IER
                self.create_red_ier(item)
            elif item["itemType"] == "RED_POL":
                # Create a Red PoL
                self.create_red_pol(item)
            elif item["itemType"] == "ACL_RULE":
                # Create an ACL rule
                self.create_acl_rule(item)
            elif item["itemType"] == "SERVICES":
                # Create the list of services
                self.create_services_list(item)
            elif item["itemType"] == "PORTS":
                # Create the list of ports
                self.create_ports_list(item)
            elif item["itemType"] == "ACTIONS":
                # Get the action information
                self.get_action_info(item)
            elif item["itemType"] == "STEPS":
                # Get the steps information
                self.get_steps_info(item)
            else:
                # Do nothing (bad formatting)
                pass

        logging.info("Environment configuration loaded")
        print("Environment configuration loaded")

    def create_node(self, item):
        """
        Creates a node from config data

        Args:
            item: A config data item
        """

        # All nodes have these parameters
        node_id = item["id"]
        node_name = item["name"]
        node_base_type = item["baseType"]
        node_type = TYPE[item["nodeType"]]
        node_priority = PRIORITY[item["priority"]]
        node_hardware_state = HARDWARE_STATE[item["hardwareState"]]

        if node_base_type == "PASSIVE":
            node = PassiveNode(node_id, node_name, node_type, node_priority, node_hardware_state, self.config_values)
        elif node_base_type == "ACTIVE":
            # Active nodes have IP address, operating system state and file system state
            node_ip_address = item["ipAddress"]
            node_software_state = SOFTWARE_STATE[item["softwareState"]]
            node_file_system_state = FILE_SYSTEM_STATE[item["fileSystemState"]]
            node = ActiveNode(node_id, node_name, node_type, node_priority, node_hardware_state, node_ip_address, node_software_state, node_file_system_state, self.config_values)
        elif node_base_type == "SERVICE":
            # Service nodes have IP address, operating system state, file system state and list of services
            node_ip_address = item["ipAddress"]
            node_software_state = SOFTWARE_STATE[item["softwareState"]]
            node_file_system_state = FILE_SYSTEM_STATE[item["fileSystemState"]]
            node = ServiceNode(node_id, node_name, node_type, node_priority, node_hardware_state, node_ip_address, node_software_state, node_file_system_state, self.config_values)
            node_services = item["services"]
            for service in node_services:
                service_protocol = service["name"]
                service_port = service["port"]
                service_state = SOFTWARE_STATE[service["state"]]
                node.add_service(Service(service_protocol, service_port, service_state))
        else:
            # Bad formatting
            pass

        # Copy the node for the reference version
        node_ref = copy.deepcopy(node)

        # Add node to node dictionary
        self.nodes[node_id] = node

        # Add reference node to reference node dictionary
        self.nodes_reference[node_id] = node_ref

        # Add node to network
        self.network.add_nodes_from([node])

        # Add node to network (reference)
        self.network_reference.add_nodes_from([node_ref])

    def create_link(self, item):
        """
        Creates a link from config data

        Args:
            item: A config data item
        """

        link_id = item["id"]
        link_name = item["name"]
        link_bandwidth = item["bandwidth"]
        link_source = item["source"]
        link_destination = item["destination"]

        source_node = self.nodes[link_source]
        dest_node = self.nodes[link_destination]

        # Add link to network
        self.network.add_edge(source_node, dest_node, id=link_name)

        # Add link to link dictionary
        self.links[link_name] = Link(link_id, link_bandwidth, source_node.get_name(), dest_node.get_name(), self.services_list)

        # Reference
        source_node_ref = self.nodes_reference[link_source]
        dest_node_ref = self.nodes_reference[link_destination]

        # Add link to network (reference)
        self.network_reference.add_edge(source_node_ref, dest_node_ref, id=link_name)

        # Add link to link dictionary (reference)
        self.links_reference[link_name] = Link(link_id, link_bandwidth, source_node_ref.get_name(), dest_node_ref.get_name(), self.services_list)

    def create_green_ier(self, item):
        """
        Creates a green IER from config data

        Args:
            item: A config data item
        """

        ier_id = item["id"]
        ier_start_step = item["startStep"]
        ier_end_step = item["endStep"]
        ier_load = item["load"]
        ier_protocol = item["protocol"]
        ier_port = item["port"]
        ier_source = item["source"]
        ier_destination = item["destination"]
        ier_mission_criticality = item["missionCriticality"]

        # Create IER and add to green IER dictionary
        self.green_iers[ier_id] = IER(ier_id, ier_start_step, ier_end_step, ier_load, ier_protocol, ier_port, ier_source, ier_destination, ier_mission_criticality)

    def create_red_ier(self, item):
        """
        Creates a red IER from config data

        Args:
            item: A config data item
        """

        ier_id = item["id"]
        ier_start_step = item["startStep"]
        ier_end_step = item["endStep"]
        ier_load = item["load"]
        ier_protocol = item["protocol"]
        ier_port = item["port"]
        ier_source = item["source"]
        ier_destination = item["destination"]
        ier_mission_criticality = item["missionCriticality"]

        # Create IER and add to red IER dictionary
        self.red_iers[ier_id] = IER(ier_id, ier_start_step, ier_end_step, ier_load, ier_protocol, ier_port, ier_source, ier_destination, ier_mission_criticality)

    def create_green_pol(self, item):
        """
        Creates a green PoL object from config data

        Args:
            item: A config data item
        """

        pol_id = item["id"]
        pol_start_step = item["startStep"]
        pol_end_step = item["endStep"]
        pol_node = item["nodeId"]
        pol_type = NODE_POL_TYPE[item["type"]]  

        # State depends on whether this is Operating, O/S, file system or Service PoL type
        if pol_type == NODE_POL_TYPE.OPERATING:
            pol_state = HARDWARE_STATE[item["state"]]
            pol_protocol = ""
        elif pol_type == NODE_POL_TYPE.FILE:
            pol_state = FILE_SYSTEM_STATE[item["state"]]
            pol_protocol = ""
        else:
            pol_protocol = item["protocol"]
            pol_state = SOFTWARE_STATE[item["state"]]

        self.node_pol[pol_id] = NodeStateInstructionGreen(pol_id, pol_start_step, pol_end_step, pol_node, pol_type, pol_protocol, pol_state)

    def create_red_pol(self, item):
        """
        Creates a red PoL object from config data

        Args:
            item: A config data item
        """

        pol_id = item["id"]
        pol_start_step = item["startStep"]
        pol_end_step = item["endStep"]
        pol_target_node_id = item["targetNodeId"]
        pol_initiator = NODE_POL_INITIATOR[item["initiator"]]
        pol_type = NODE_POL_TYPE[item["type"]]
        pol_protocol = item["protocol"]

        # State depends on whether this is Operating, O/S, file system or Service PoL type
        if pol_type == NODE_POL_TYPE.OPERATING:
            pol_state = HARDWARE_STATE[item["state"]]
        elif pol_type == NODE_POL_TYPE.FILE:
            pol_state = FILE_SYSTEM_STATE[item["state"]]
        else:
            pol_state = SOFTWARE_STATE[item["state"]]

        pol_source_node_id = item["sourceNodeId"]
        pol_source_node_service = item["sourceNodeService"]
        pol_source_node_service_state = item["sourceNodeServiceState"]

        self.red_node_pol[pol_id] = NodeStateInstructionRed(pol_id, pol_start_step, pol_end_step, pol_target_node_id, pol_initiator, pol_type, pol_protocol, pol_state, pol_source_node_id, pol_source_node_service, pol_source_node_service_state)

    def create_acl_rule(self, item):
        """
        Creates an ACL rule from config data

        Args:
            item: A config data item
        """

        acl_rule_permission = item["permission"]
        acl_rule_source = item["source"]
        acl_rule_destination = item["destination"]
        acl_rule_protocol = item["protocol"]
        acl_rule_port = item["port"]

        self.acl.add_rule(acl_rule_permission, acl_rule_source, acl_rule_destination, acl_rule_protocol, acl_rule_port)

    def create_services_list(self, services):
        """
        Creates a list of services (enum) from config data

        Args:
            item: A config data item representing the services
        """

        service_list = services["serviceList"]

        for service in service_list:
            service_name = service["name"]
            self.services_list.append(service_name)

        # Set the number of services
        self.num_services = len(self.services_list)

    def create_ports_list(self, ports):
        """
        Creates a list of ports from config data

        Args:
            item: A config data item representing the ports
        """

        ports_list = ports["portsList"]

        for port in ports_list:
            port_value = port["port"]
            self.ports_list.append(port_value)

        # Set the number of ports
        self.num_ports = len(self.ports_list)

    def get_action_info(self, action_info):
        """
        Extracts action_info

        Args:
            item: A config data item representing action info
        """

        self.action_type = ACTION_TYPE[action_info["type"]]


    def get_steps_info(self, steps_info):
        """
        Extracts steps_info

        Args:
            item: A config data item representing steps info
        """

        self.episode_steps = int(steps_info["steps"])
        logging.info("Training episodes have " + str(self.episode_steps) + " steps")

    def reset_environment(self):
        """
        # Resets environment using config data config data in order to build the environment configuration
        """ 

        for item in self.config_data:
            if item["itemType"] == "NODE":
                # Reset a node's state (normal and reference)
                self.reset_node(item)           
            elif item["itemType"] == "ACL_RULE":
                # Create an ACL rule (these are cleared on reset, so just need to recreate them)
                self.create_acl_rule(item)
            else:
                # Do nothing (bad formatting or not relevant to reset)
                pass


        # Reset the IER status so they are not running initially
        # Green IERs
        for ier_key, ier_value in self.green_iers.items():
            ier_value.set_is_running(False)
        # Red IERs
        for ier_key, ier_value in self.red_iers.items():
            ier_value.set_is_running(False)

    def reset_node(self, item):
        """
        Resets the statuses of a node

        Args:
            item: A config data item
        """

        # All nodes have these parameters
        node_id = item["id"]
        node_base_type = item["baseType"]
        node_hardware_state = HARDWARE_STATE[item["hardwareState"]]

        node = self.nodes[node_id]
        node_ref = self.nodes_reference[node_id]

        # Reset the hardware state (common for all node types)
        node.set_state(node_hardware_state)
        node_ref.set_state(node_hardware_state)

        if node_base_type == "ACTIVE":
            # Active nodes have operating system state
            node_software_state = SOFTWARE_STATE[item["softwareState"]]
            node_file_system_state = FILE_SYSTEM_STATE[item["fileSystemState"]]
            node.set_os_state(node_software_state)
            node_ref.set_os_state(node_software_state)
            node.set_file_system_state(node_file_system_state)
            node_ref.set_file_system_state(node_file_system_state)
        elif node_base_type == "SERVICE":
            # Service nodes have operating system state and list of services
            node_software_state = SOFTWARE_STATE[item["softwareState"]]
            node_file_system_state = FILE_SYSTEM_STATE[item["fileSystemState"]]
            node.set_os_state(node_software_state)
            node_ref.set_os_state(node_software_state)
            node.set_file_system_state(node_file_system_state)
            node_ref.set_file_system_state(node_file_system_state)
            # Update service states
            node_services = item["services"]
            for service in node_services:
                service_protocol = service["name"]
                service_state = SOFTWARE_STATE[service["state"]]
                # Update node service state
                node.set_service_state(service_protocol, service_state)
                # Update reference node service state
                node_ref.set_service_state(service_protocol, service_state)
        else:
            # Bad formatting
            pass







