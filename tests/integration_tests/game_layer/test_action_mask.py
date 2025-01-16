# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
from primaite.session.environment import PrimaiteGymEnv
from primaite.simulator.network.hardware.node_operating_state import NodeOperatingState
from primaite.simulator.network.hardware.nodes.host.host_node import HostNode
from primaite.simulator.system.services.service import ServiceOperatingState
from tests.conftest import TEST_ASSETS_ROOT

CFG_PATH = TEST_ASSETS_ROOT / "configs/test_primaite_session.yaml"


def test_mask_contents_correct():
    env = PrimaiteGymEnv(CFG_PATH)
    game = env.game
    sim = game.simulation
    net = sim.network
    mask = game.action_mask("defender")
    agent = env.agent
    action_map = agent.action_manager.action_map

    # CHECK NIC ENABLE/DISABLE ACTIONS
    for action_num, action in action_map.items():
        mask = game.action_mask("defender")
        act_type, act_params = action

        if act_type == "node_nic_enable":
            node_name = act_params["node_name"]
            node_obj = net.get_node_by_hostname(node_name)
            nic_obj = node_obj.network_interface[act_params["nic_id"] + 1]
            assert nic_obj.enabled
            assert not mask[action_num]
            nic_obj.disable()
            mask = game.action_mask("defender")
            assert mask[action_num]
            nic_obj.enable()

        if act_type == "node_nic_disable":
            node_name = act_params["node_name"]
            node_obj = net.get_node_by_hostname(node_name)
            nic_obj = node_obj.network_interface[act_params["nic_id"] + 1]
            assert nic_obj.enabled
            assert mask[action_num]
            nic_obj.disable()
            mask = game.action_mask("defender")
            assert not mask[action_num]
            nic_obj.enable()

        if act_type == "router_acl_add_rule":
            assert mask[action_num]

        if act_type == "router_acl_remove_rule":
            assert mask[action_num]

        if act_type == "node_reset":
            node_name = act_params["node_name"]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "node_shutdown":
            node_name = act_params["node_name"]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "node_os_scan":
            node_name = act_params["node_name"]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "node_startup":
            node_name = act_params["node_name"]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "do_nothing":
            assert mask[action_num]

        if act_type == "node_service_disable":
            assert mask[action_num]

        if act_type in ["node_service_scan", "node_service_stop", "node_service_pause"]:
            node_name = act_params["node_name"]
            service_name = act_params["service_name"]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.DISABLED
            mask = game.action_mask("defender")
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type == "node_service_resume":
            node_name = act_params["node_name"]
            service_name = act_params["service_name"]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.PAUSED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type == "node_service_start":
            node_name = act_params["node_name"]
            service_name = act_params["service_name"]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.STOPPED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type == "node_service_enable":
            node_name = act_params["node_name"]
            service_name = act_params["service_name"]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.DISABLED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type in ["node_file_scan", "node_file_checkhash", "node_file_delete"]:
            node_name = act_params["node_name"]
            folder_name = act_params["folder_name"]
            file_name = act_params["file_name"]
            node_obj = net.get_node_by_hostname(node_name)
            file_obj = node_obj.file_system.get_file(folder_name, file_name, include_deleted=True)
            assert not file_obj.deleted
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.DISABLED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING
