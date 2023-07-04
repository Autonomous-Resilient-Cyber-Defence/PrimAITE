import pytest

from primaite.config.lay_down_config import data_manipulation_config_path
from primaite.nodes.node_state_instruction_red import NodeStateInstructionRed
from tests import TEST_CONFIG_ROOT


@pytest.mark.parametrize(
    "temp_primaite_session",
    [
        [
            TEST_CONFIG_ROOT / "test_random_red_main_config.yaml",
            data_manipulation_config_path(),
        ]
    ],
    indirect=True,
)
def test_random_red_agent_behaviour(temp_primaite_session):
    """Test that red agent POL is randomised each episode."""
    list_of_node_instructions = []

    with temp_primaite_session as session:
        session.evaluate()
        list_of_node_instructions.append(session.env.red_node_pol)

        session.evaluate()
        list_of_node_instructions.append(session.env.red_node_pol)

    # compare instructions to make sure that red instructions are truly random
    for index, instruction in enumerate(list_of_node_instructions):
        for key in list_of_node_instructions[index].keys():
            instruction: NodeStateInstructionRed = list_of_node_instructions[index][key]
            print(f"run {index}")
            print(f"{key} start step: {instruction.get_start_step()}")
            print(f"{key} end step: {instruction.get_end_step()}")
            print(f"{key} target node id: {instruction.get_target_node_id()}")
            print("")
    assert list_of_node_instructions[0].__ne__(list_of_node_instructions[1])
