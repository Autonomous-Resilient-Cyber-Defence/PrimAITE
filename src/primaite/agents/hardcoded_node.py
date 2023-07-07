from primaite.agents.agent import HardCodedAgentSessionABC
from primaite.agents.utils import get_new_action, transform_action_node_enum, transform_change_obs_readable


class HardCodedNodeAgent(HardCodedAgentSessionABC):
    """An Agent Session class that implements a deterministic Node agent."""

    def _calculate_action(self, obs):
        """
        Calculate a good node-based action for the blue agent to take.

        TODO: Add params and return in docstring.
        TODO: Typehint params and return.
        """
        action_dict = self._env.action_dict
        r_obs = transform_change_obs_readable(obs)
        _, o, os, *s = r_obs

        if len(r_obs) == 4:  # only 1 service
            s = [*s]

        # Check in order of most important states (order doesn't currently
        # matter, but it probably should)
        # First see if any OS states are compromised
        for x, os_state in enumerate(os):
            if os_state == "COMPROMISED":
                action_node_id = x + 1
                action_node_property = "OS"
                property_action = "PATCHING"
                action_service_index = 0  # does nothing isn't relevant for os
                action = [
                    action_node_id,
                    action_node_property,
                    property_action,
                    action_service_index,
                ]
                action = transform_action_node_enum(action)
                action = get_new_action(action, action_dict)
                # We can only perform 1 action on each step
                return action

        # Next, see if any Services are compromised
        # We fix the compromised state before overwhelemd state,
        # If a compromised entry node is fixed before the overwhelmed state is triggered, instruction is ignored
        for service_num, service in enumerate(s):
            for x, service_state in enumerate(service):
                if service_state == "COMPROMISED":
                    action_node_id = x + 1
                    action_node_property = "SERVICE"
                    property_action = "PATCHING"
                    action_service_index = service_num

                    action = [
                        action_node_id,
                        action_node_property,
                        property_action,
                        action_service_index,
                    ]
                    action = transform_action_node_enum(action)
                    action = get_new_action(action, action_dict)
                    # We can only perform 1 action on each step
                    return action

        # Next, See if any services are overwhelmed
        # perhaps this should be fixed automatically when the compromised PCs issues are also resolved
        # Currently there's no reason that an Overwhelmed state cannot be resolved before resolving the compromised PCs

        for service_num, service in enumerate(s):
            for x, service_state in enumerate(service):
                if service_state == "OVERWHELMED":
                    action_node_id = x + 1
                    action_node_property = "SERVICE"
                    property_action = "PATCHING"
                    action_service_index = service_num

                    action = [
                        action_node_id,
                        action_node_property,
                        property_action,
                        action_service_index,
                    ]
                    action = transform_action_node_enum(action)
                    action = get_new_action(action, action_dict)
                    # We can only perform 1 action on each step
                    return action

        # Finally, turn on any off nodes
        for x, operating_state in enumerate(o):
            if os_state == "OFF":
                action_node_id = x + 1
                action_node_property = "OPERATING"
                property_action = "ON"  # Why reset it when we can just turn it on
                action_service_index = 0  # does nothing isn't relevant for operating state
                action = [
                    action_node_id,
                    action_node_property,
                    property_action,
                    action_service_index,
                ]
                action = transform_action_node_enum(action, action_dict)
                action = get_new_action(action, action_dict)
                # We can only perform 1 action on each step
                return action

        # If no good actions, just go with an action that wont do any harm
        action_node_id = 1
        action_node_property = "NONE"
        property_action = "ON"
        action_service_index = 0
        action = [
            action_node_id,
            action_node_property,
            property_action,
            action_service_index,
        ]
        action = transform_action_node_enum(action)
        action = get_new_action(action, action_dict)

        return action
