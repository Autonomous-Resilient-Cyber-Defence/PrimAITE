"""Test the account module of the simulator."""
from primaite.simulator.domain.account import Account, AccountType


def test_account_serialise():
    """Test that an account can be serialised."""
    acct = Account(username="Jake", password="JakePass1!", account_type=AccountType.USER)
    serialised = acct.model_dump_json()
    print(serialised)


def test_account_deserialise():
    """Test that an account can be deserialised."""
    acct_json = (
        '{"uuid":"dfb2bcaa-d3a1-48fd-af3f-c943354622b4","num_logons":0,"num_logoffs":0,"num_group_changes":0,'
        '"username":"Jake","password":"JakePass1!","account_type":2,"status":2,"action_manager":null}'
    )
    acct = Account.model_validate_json(acct_json)
