from datetime import datetime

from primaite import _PRIMAITE_ROOT

SIM_OUTPUT = None
"A path at the repo root dir to use temporarily for sim output testing while in dev."
# TODO: Remove once we integrate the simulation into PrimAITE and it uses the primaite session path

if not SIM_OUTPUT:
    session_timestamp = datetime.now()
    date_dir = session_timestamp.strftime("%Y-%m-%d")
    sim_path = session_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    SIM_OUTPUT = _PRIMAITE_ROOT.parent.parent / "simulation_output" / date_dir / sim_path
    SIM_OUTPUT.mkdir(exist_ok=True, parents=True)
