# © Crown-owned copyright 2023, Defence Science and Technology Laboratory UK
from typing import Dict, List, Union

import numpy as np

from primaite.acl.access_control_list import AccessControlList
from primaite.acl.acl_rule import ACLRule
from primaite.agents.hardcoded_abc import HardCodedAgentSessionABC
from primaite.agents.utils import (
    get_new_action,
    get_node_of_ip,
    transform_action_acl_enum,
    transform_change_obs_readable,
)
from primaite.common.custom_typing import NodeUnion
from primaite.common.enums import HardCodedAgentView
from primaite.nodes.active_node import ActiveNode
from primaite.nodes.service_node import ServiceNode
from primaite.pol.ier import IER


class HardCodedACLAgent(HardCodedAgentSessionABC):
    """An Agent Session class that implements a deterministic ACL agent."""

    def _calculate_action(self, obs: np.ndarray) -> int:
        if self._training_config.hard_coded_agent_view == HardCodedAgentView.BASIC:
            # Basic view action using only the current observation
            return self._calculate_action_basic_view(obs)
        else:
            # full view action using observation space, action
            # history and reward feedback
            return self._calculate_action_full_view(obs)

    def get_blocked_green_iers(
        self, green_iers: Dict[str, IER], acl: AccessControlList, nodes: Dict[str, NodeUnion]
    ) -> Dict[str, IER]:
        """Get blocked green IERs.

        :param green_iers: Green IERs to check for being
        :type green_iers: Dict[str, IER]
        :param acl: Firewall rules
        :type acl: AccessControlList
        :param nodes: Nodes in the network
        :type nodes: Dict[str,NodeUnion]
        :return: Same as `green_iers` input dict, but filtered to only contain the blocked ones.
        :rtype: Dict[str, IER]
        """
        blocked_green_iers = {}

        for green_ier_id, green_ier in green_iers.items():
            source_node_id = green_ier.get_source_node_id()
            source_node_address = nodes[source_node_id].ip_address
            dest_node_id = green_ier.get_dest_node_id()
            dest_node_address = nodes[dest_node_id].ip_address
            protocol = green_ier.get_protocol()  # e.g. 'TCP'
            port = green_ier.get_port()

            # Can be blocked by an ACL or by default (no allow rule exists)
            if acl.is_blocked(source_node_address, dest_node_address, protocol, port):
                blocked_green_iers[green_ier_id] = green_ier

        return blocked_green_iers

    def get_matching_acl_rules_for_ier(
        self, ier: IER, acl: AccessControlList, nodes: Dict[str, NodeUnion]
    ) -> Dict[int, ACLRule]:
        """Get list of ACL rules which are relevant to an IER.

        :param ier: Information Exchange Request to query against the ACL list
        :type ier: IER
        :param acl: Firewall rules
        :type acl: AccessControlList
        :param nodes: Nodes in the network
        :type nodes: Dict[str,NodeUnion]
        :return: _description_
        :rtype: _type_
        """
        source_node_id = ier.get_source_node_id()
        source_node_address = nodes[source_node_id].ip_address
        dest_node_id = ier.get_dest_node_id()
        dest_node_address = nodes[dest_node_id].ip_address
        protocol = ier.get_protocol()  # e.g. 'TCP'
        port = ier.get_port()
        matching_rules = acl.get_relevant_rules(source_node_address, dest_node_address, protocol, port)
        return matching_rules

    def get_blocking_acl_rules_for_ier(
        self, ier: IER, acl: AccessControlList, nodes: Dict[str, NodeUnion]
    ) -> Dict[int, ACLRule]:
        """
        Get blocking ACL rules for an IER.

        .. warning::
            Can return empty dict but IER can still be blocked by default
            (No ALLOW rule, therefore blocked).

        :param ier: Information Exchange Request to query against the ACL list
        :type ier: IER
        :param acl: Firewall rules
        :type acl: AccessControlList
        :param nodes: Nodes in the network
        :type nodes: Dict[str,NodeUnion]
        :return: _description_
        :rtype: _type_
        """
        matching_rules = self.get_matching_acl_rules_for_ier(ier, acl, nodes)

        blocked_rules = {}
        for rule_key, rule_value in matching_rules.items():
            if rule_value.get_permission() == "DENY":
                blocked_rules[rule_key] = rule_value

        return blocked_rules

    def get_allow_acl_rules_for_ier(
        self, ier: IER, acl: AccessControlList, nodes: Dict[str, NodeUnion]
    ) -> Dict[int, ACLRule]:
        """Get all allowing ACL rules for an IER.

        :param ier: Information Exchange Request to query against the ACL list
        :type ier: IER
        :param acl: Firewall rules
        :type acl: AccessControlList
        :param nodes: Nodes in the network
        :type nodes: Dict[str,NodeUnion]
        :return: _description_
        :rtype: _type_
        """
        matching_rules = self.get_matching_acl_rules_for_ier(ier, acl, nodes)

        allowed_rules = {}
        for rule_key, rule_value in matching_rules.items():
            if rule_value.get_permission() == "ALLOW":
                allowed_rules[rule_key] = rule_value

        return allowed_rules

    def get_matching_acl_rules(
        self,
        source_node_id: str,
        dest_node_id: str,
        protocol: str,
        port: str,
        acl: AccessControlList,
        nodes: Dict[str, Union[ServiceNode, ActiveNode]],
        services_list: List[str],
    ) -> Dict[int, ACLRule]:
        """Filter ACL rules to only those which are relevant to the specified nodes.

        :param source_node_id: Source node
        :type source_node_id: str
        :param dest_node_id: Destination nodes
        :type dest_node_id: str
        :param protocol: Network protocol
        :type protocol: str
        :param port: Network port
        :type port: str
        :param acl: Access Control list which will be filtered
        :type acl: AccessControlList
        :param nodes: The environment's node directory.
        :type nodes: Dict[str, Union[ServiceNode, ActiveNode]]
        :param services_list: List of services registered for the environment.
        :type services_list: List[str]
        :return: Filtered version of 'acl'
        :rtype: Dict[str, ACLRule]
        """
        if source_node_id != "ANY":
            source_node_address = nodes[str(source_node_id)].ip_address
        else:
            source_node_address = source_node_id

        if dest_node_id != "ANY":
            dest_node_address = nodes[str(dest_node_id)].ip_address
        else:
            dest_node_address = dest_node_id

        if protocol != "ANY":
            protocol = services_list[protocol - 1]  # -1 as dont have to account for ANY in list of services
            # TODO: This should throw an error because protocol is a string

        matching_rules = acl.get_relevant_rules(source_node_address, dest_node_address, protocol, port)
        return matching_rules

    def get_allow_acl_rules(
        self,
        source_node_id: int,
        dest_node_id: str,
        protocol: int,
        port: str,
        acl: AccessControlList,
        nodes: Dict[str, NodeUnion],
        services_list: List[str],
    ) -> Dict[int, ACLRule]:
        """List ALLOW rules relating to specified nodes.

        :param source_node_id: Source node id
        :type source_node_id: int
        :param dest_node_id: Destination node
        :type dest_node_id: str
        :param protocol: Network protocol
        :type protocol: int
        :param port: Port
        :type port: str
        :param acl: Firewall ruleset which is applied to the network
        :type acl: AccessControlList
        :param nodes: The simulation's node store
        :type nodes: Dict[str, NodeUnion]
        :param services_list: Services list
        :type services_list: List[str]
        :return: Filtered ACL Rule directory which includes only those rules which affect the specified source and
            desination nodes
        :rtype: Dict[str, ACLRule]
        """
        matching_rules = self.get_matching_acl_rules(
            source_node_id,
            dest_node_id,
            protocol,
            port,
            acl,
            nodes,
            services_list,
        )

        allowed_rules = {}
        for rule_key, rule_value in matching_rules.items():
            if rule_value.get_permission() == "ALLOW":
                allowed_rules[rule_key] = rule_value

        return allowed_rules

    def get_deny_acl_rules(
        self,
        source_node_id: int,
        dest_node_id: str,
        protocol: int,
        port: str,
        acl: AccessControlList,
        nodes: Dict[str, NodeUnion],
        services_list: List[str],
    ) -> Dict[int, ACLRule]:
        """List DENY rules relating to specified nodes.

        :param source_node_id: Source node id
        :type source_node_id: int
        :param dest_node_id: Destination node
        :type dest_node_id: str
        :param protocol: Network protocol
        :type protocol: int
        :param port: Port
        :type port: str
        :param acl: Firewall ruleset which is applied to the network
        :type acl: AccessControlList
        :param nodes: The simulation's node store
        :type nodes: Dict[str, NodeUnion]
        :param services_list: Services list
        :type services_list: List[str]
        :return: Filtered ACL Rule directory which includes only those rules which affect the specified source and
            desination nodes
        :rtype: Dict[str, ACLRule]
        """
        matching_rules = self.get_matching_acl_rules(
            source_node_id,
            dest_node_id,
            protocol,
            port,
            acl,
            nodes,
            services_list,
        )

        allowed_rules = {}
        for rule_key, rule_value in matching_rules.items():
            if rule_value.get_permission() == "DENY":
                allowed_rules[rule_key] = rule_value

        return allowed_rules

    def _calculate_action_full_view(self, obs: np.ndarray) -> int:
        """
        Calculate a good acl-based action for the blue agent to take.

        Knowledge of just the observation space is insufficient for a perfect solution, as we need to know:

            - Which ACL rules already exist, - otherwise:
                 - The agent would perminently get stuck in a loop of performing the same action over and over.
                 (best action is to block something, but its already blocked but doesn't know this)
                 - The agent would be unable to interact with existing rules (e.g. how would it know to delete a rule,
                 if it doesnt know what rules exist)
            - The Green IERs (optional) - It often needs to know which traffic it should be allowing. For example
             in the default config one of the green IERs is blocked by default, but it has no way of knowing this
             based on the observation space. Additionally, potentially in the future, once a node state
             has been fixed (no longer compromised), it needs a way to know it should reallow traffic.
             A RL agent can learn what the green IERs are on its own - but the rule based agent cannot easily do this.

        There doesn't seem like there's much that can be done if an Operating or OS State is compromised

        If a service node becomes compromised there's a decision to make - do we block that service?
        Pros: It cannot launch an attack on another node, so the node will not be able to be OVERWHELMED
        Cons: Will block a green IER, decreasing the reward
        We decide to block the service.

        Potentially a better solution (for the reward) would be to block the incomming traffic from compromised
        nodes once a service becomes overwhelmed. However currently the ACL action space has no way of reversing
        an overwhelmed state, so we don't do this.

        :param obs: current observation from the gym environment
        :type obs: np.ndarray
        :return: Optimal action to take in the environment (chosen from the discrete action space)
        :rtype: int
        """
        # obs = convert_to_old_obs(obs)
        r_obs = transform_change_obs_readable(obs)
        _, _, _, *s = r_obs

        if len(r_obs) == 4:  # only 1 service
            s = [*s]

        # 1. Check if node is compromised. If so we want to block its outwards services
        # a. If it is comprimised check if there's an allow rule we should delete.
        #   cons: might delete a multi-rule from any source node (ANY -> x)
        # b. OPTIONAL (Deny rules not needed): Check if there already exists an existing Deny Rule so not to duplicate
        # c. OPTIONAL (no allow rule = blocked): Add a DENY rule
        found_action = False
        for service_num, service_states in enumerate(s):
            for x, service_state in enumerate(service_states):
                if service_state == "COMPROMISED":
                    action_source_id = x + 1  # +1 as 0 is any
                    action_destination_id = "ANY"
                    action_protocol = service_num + 1  # +1 as 0 is any
                    action_port = "ANY"

                    allow_rules = self.get_allow_acl_rules(
                        action_source_id,
                        action_destination_id,
                        action_protocol,
                        action_port,
                        self._env.acl,
                        self._env.nodes,
                        self._env.services_list,
                    )
                    deny_rules = self.get_deny_acl_rules(
                        action_source_id,
                        action_destination_id,
                        action_protocol,
                        action_port,
                        self._env.acl,
                        self._env.nodes,
                        self._env.services_list,
                    )
                    if len(allow_rules) > 0:
                        # Check if there's an allow rule we should delete
                        rule = list(allow_rules.values())[0]
                        action_decision = "DELETE"
                        action_permission = "ALLOW"
                        action_source_ip = rule.get_source_ip()
                        action_source_id = int(get_node_of_ip(action_source_ip, self._env.nodes))
                        action_destination_ip = rule.get_dest_ip()
                        action_destination_id = int(get_node_of_ip(action_destination_ip, self._env.nodes))
                        action_protocol_name = rule.get_protocol()
                        action_protocol = (
                            self._env.services_list.index(action_protocol_name) + 1
                        )  # convert name e.g. 'TCP' to index
                        action_port_name = rule.get_port()
                        action_port = (
                            self._env.ports_list.index(action_port_name) + 1
                        )  # convert port name e.g. '80' to index

                        found_action = True
                        break
                    elif len(deny_rules) > 0:
                        # TODO OPTIONAL
                        # If there's already a DENY RULE, that blocks EVERYTHING from the source ip we don't need
                        # to create another
                        # Check to see if the DENY rule really blocks everything (ANY) or just a specific rule
                        continue
                    else:
                        # TODO OPTIONAL: Add a DENY rule, optional as by default no allow rule == blocked
                        action_decision = "CREATE"
                        action_permission = "DENY"
                        break
            if found_action:
                break

        # 2. If NO Node is Comprimised, or the node has already been blocked, check the green IERs and
        #  add an Allow rule if the green IER is being blocked.
        # a.  OPTIONAL - NOT IMPLEMENTED (optional as a deny rule does not overwrite an allow rule):
        # If there's a DENY rule delete it if:
        #    - There isn't already a deny rule
        #    - It doesnt allows a comprimised node to become operational.
        # b. Add an ALLOW rule if:
        #     - There isn't already an allow rule
        #     - It doesnt allows a comprimised node to become operational

        if not found_action:
            # Which Green IERS are blocked
            blocked_green_iers = self.get_blocked_green_iers(self._env.green_iers, self._env.acl, self._env.nodes)
            for ier_key, ier in blocked_green_iers.items():
                # Which ALLOW rules are allowing this IER (none)
                allowing_rules = self.get_allow_acl_rules_for_ier(ier, self._env.acl, self._env.nodes)

                # If there are no blocking rules, it may be being blocked by default
                # If there is already an allow rule
                node_id_to_check = int(ier.get_source_node_id())
                service_name_to_check = ier.get_protocol()
                service_id_to_check = self._env.services_list.index(service_name_to_check)

                # Service state of the the source node in the ier
                service_state = s[service_id_to_check][node_id_to_check - 1]

                if len(allowing_rules) == 0 and service_state != "COMPROMISED":
                    action_decision = "CREATE"
                    action_permission = "ALLOW"
                    action_source_id = int(ier.get_source_node_id())
                    action_destination_id = int(ier.get_dest_node_id())
                    action_protocol_name = ier.get_protocol()
                    action_protocol = (
                        self._env.services_list.index(action_protocol_name) + 1
                    )  # convert name e.g. 'TCP' to index
                    action_port_name = ier.get_port()
                    action_port = (
                        self._env.ports_list.index(action_port_name) + 1
                    )  # convert port name e.g. '80' to index

                    found_action = True
                    break

        if found_action:
            action = [
                action_decision,
                action_permission,
                action_source_id,
                action_destination_id,
                action_protocol,
                action_port,
            ]
            action = transform_action_acl_enum(action)
            action = get_new_action(action, self._env.action_dict)
        else:
            # If no good/useful action has been found, just perform a nothing action
            action = ["NONE", "ALLOW", "ANY", "ANY", "ANY", "ANY"]
            action = transform_action_acl_enum(action)
            action = get_new_action(action, self._env.action_dict)
        return action

    def _calculate_action_basic_view(self, obs: np.ndarray) -> int:
        """
        Calculate a good acl-based action for the blue agent to take.

        Uses ONLY information from the current observation with NO knowledge
        of previous actions taken and NO reward feedback.

        We rely on randomness to select the precise action, as we want to
        block all traffic originating from a compromised node, without being
        able to tell:
            1. Which ACL rules already exist
            2. Which actions the agent has already tried.

        There is a high probability that the correct rule will not be deleted
        before the state becomes overwhelmed.

        Currently, a deny rule does not overwrite an allow rule. The allow
        rules must be deleted.

        :param obs: current observation from the gym environment
        :type obs: np.ndarray
        :return: Optimal action to take in the environment (chosen from the discrete action space)
        :rtype: int
        """
        action_dict = self._env.action_dict
        r_obs = transform_change_obs_readable(obs)
        _, o, _, *s = r_obs

        if len(r_obs) == 4:  # only 1 service
            s = [*s]

        number_of_nodes = len([i for i in o if i != "NONE"])  # number of nodes (not links)
        for service_num, service_states in enumerate(s):
            comprimised_states = [n for n, i in enumerate(service_states) if i == "COMPROMISED"]
            if len(comprimised_states) == 0:
                # No states are COMPROMISED, try the next service
                continue

            compromised_node = np.random.choice(comprimised_states) + 1  # +1 as 0 would be any
            action_decision = "DELETE"
            action_permission = "ALLOW"
            action_source_ip = compromised_node
            # Randomly select a destination ID to block
            action_destination_ip = np.random.choice(list(range(1, number_of_nodes + 1)) + ["ANY"])
            action_destination_ip = (
                int(action_destination_ip) if action_destination_ip != "ANY" else action_destination_ip
            )
            action_protocol = service_num + 1  # +1 as 0 is any
            # Randomly select a port to block
            # Bad assumption that number of protocols equals number of ports
            # AND no rules exist with an ANY port
            action_port = np.random.choice(list(range(1, len(s) + 1)))

            action = [
                action_decision,
                action_permission,
                action_source_ip,
                action_destination_ip,
                action_protocol,
                action_port,
            ]
            action = transform_action_acl_enum(action)
            action = get_new_action(action, action_dict)
            # We can only perform 1 action on each step
            return action

        # If no good/useful action has been found, just perform a nothing action
        nothing_action = ["NONE", "ALLOW", "ANY", "ANY", "ANY", "ANY"]
        nothing_action = transform_action_acl_enum(nothing_action)
        nothing_action = get_new_action(nothing_action, action_dict)
        return nothing_action
