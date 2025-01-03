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
    node_list = agent.action_manager.node_names
    action_map = agent.action_manager.action_map

    # CHECK NIC ENABLE/DISABLE ACTIONS
    for action_num, action in action_map.items():
        mask = game.action_mask("defender")
        act_type, act_params = action

        if act_type == "NODE_NIC_ENABLE":
            node_name = node_list[act_params["node_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            nic_obj = node_obj.network_interface[act_params["nic_id"] + 1]
            assert nic_obj.enabled
            assert not mask[action_num]
            nic_obj.disable()
            mask = game.action_mask("defender")
            assert mask[action_num]
            nic_obj.enable()

        if act_type == "NODE_NIC_DISABLE":
            node_name = node_list[act_params["node_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            nic_obj = node_obj.network_interface[act_params["nic_id"] + 1]
            assert nic_obj.enabled
            assert mask[action_num]
            nic_obj.disable()
            mask = game.action_mask("defender")
            assert not mask[action_num]
            nic_obj.enable()

        if act_type == "ROUTER_ACL_ADDRULE":
            assert mask[action_num]

        if act_type == "ROUTER_ACL_REMOVERULE":
            assert mask[action_num]

        if act_type == "NODE_RESET":
            node_name = node_list[act_params["node_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "NODE_SHUTDOWN":
            node_name = node_list[act_params["node_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "NODE_OS_SCAN":
            node_name = node_list[act_params["node_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "NODE_STARTUP":
            node_name = node_list[act_params["node_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            assert node_obj.operating_state is NodeOperatingState.ON
            assert not mask[action_num]
            node_obj.operating_state = NodeOperatingState.OFF
            mask = game.action_mask("defender")
            assert mask[action_num]
            node_obj.operating_state = NodeOperatingState.ON

        if act_type == "do_nothing":
            assert mask[action_num]

        if act_type == "NODE_SERVICE_DISABLE":
            assert mask[action_num]

        if act_type in ["NODE_SERVICE_SCAN", "NODE_SERVICE_STOP", "NODE_SERVICE_PAUSE"]:
            node_name = node_list[act_params["node_id"]]
            service_name = agent.action_manager.service_names[act_params["node_id"]][act_params["service_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.DISABLED
            mask = game.action_mask("defender")
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type == "NODE_SERVICE_RESUME":
            node_name = node_list[act_params["node_id"]]
            service_name = agent.action_manager.service_names[act_params["node_id"]][act_params["service_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.PAUSED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type == "NODE_SERVICE_START":
            node_name = node_list[act_params["node_id"]]
            service_name = agent.action_manager.service_names[act_params["node_id"]][act_params["service_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.STOPPED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type == "NODE_SERVICE_ENABLE":
            node_name = node_list[act_params["node_id"]]
            service_name = agent.action_manager.service_names[act_params["node_id"]][act_params["service_id"]]
            node_obj = net.get_node_by_hostname(node_name)
            service_obj = node_obj.software_manager.software.get(service_name)
            assert service_obj.operating_state is ServiceOperatingState.RUNNING
            assert not mask[action_num]
            service_obj.operating_state = ServiceOperatingState.DISABLED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING

        if act_type in ["NODE_FILE_SCAN", "NODE_FILE_CHECKHASH", "NODE_FILE_DELETE"]:
            node_name = node_list[act_params["node_id"]]
            folder_name = agent.action_manager.get_folder_name_by_idx(act_params["node_id"], act_params["folder_id"])
            file_name = agent.action_manager.get_file_name_by_idx(
                act_params["node_id"], act_params["folder_id"], act_params["file_id"]
            )
            node_obj = net.get_node_by_hostname(node_name)
            file_obj = node_obj.file_system.get_file(folder_name, file_name, include_deleted=True)
            assert not file_obj.deleted
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.DISABLED
            mask = game.action_mask("defender")
            assert mask[action_num]
            service_obj.operating_state = ServiceOperatingState.RUNNING
