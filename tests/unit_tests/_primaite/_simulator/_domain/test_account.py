# © Crown-owned copyright 2025, Defence Science and Technology Laboratory UK
"""Test the account module of the simulator."""
import pytest

from primaite.simulator.domain.account import Account, AccountType


@pytest.fixture(scope="function")
def account() -> Account:
    acct = Account(username="Jake", password="totally_hashed_password", account_type=AccountType.USER)
    return acct


def test_original_state(account):
    """Test the original state - see if it resets properly"""
    state = account.describe_state()
    assert state["num_logons"] is 0
    assert state["num_logoffs"] is 0
    assert state["num_group_changes"] is 0
    assert state["username"] is "Jake"
    assert state["password"] is "totally_hashed_password"
    assert state["account_type"] is AccountType.USER.value
    assert state["enabled"] is True

    account.log_on()
    account.log_off()
    account.disable()

    state = account.describe_state()
    assert state["num_logons"] is 1
    assert state["num_logoffs"] is 1
    assert state["num_group_changes"] is 0
    assert state["username"] is "Jake"
    assert state["password"] is "totally_hashed_password"
    assert state["account_type"] is AccountType.USER.value
    assert state["enabled"] is False


def test_enable(account):
    """Should enable the account."""
    account.enabled = False
    account.enable()
    assert account.enabled is True


def test_disable(account):
    """Should disable the account."""
    account.enabled = True
    account.disable()
    assert account.enabled is False


def test_log_on_increments(account):
    """Should increase the log on value by 1."""
    account.num_logons = 0
    account.log_on()
    assert account.num_logons is 1


def test_log_off_increments(account):
    """Should increase the log on value by 1."""
    account.num_logoffs = 0
    account.log_off()
    assert account.num_logoffs is 1


def test_account_serialise(account):
    """Test that an account can be serialised. If pydantic throws error then this test fails."""
    serialised = account.model_dump_json()
    print(serialised)


def test_account_deserialise(account):
    """Test that an account can be deserialised. The test fails if pydantic throws an error."""
    acct_json = (
        '{"uuid":"dfb2bcaa-d3a1-48fd-af3f-c943354622b4","num_logons":0,"num_logoffs":0,"num_group_changes":0,'
        '"username":"Jake","password":"totally_hashed_password","account_type":2,"status":2,"request_manager":null}'
    )
    assert Account.model_validate_json(acct_json)


def test_describe_state(account):
    state = account.describe_state()
    assert state["num_logons"] is 0
    assert state["num_logoffs"] is 0
    assert state["num_group_changes"] is 0
    assert state["username"] is "Jake"
    assert state["password"] is "totally_hashed_password"
    assert state["account_type"] is AccountType.USER.value
    assert state["enabled"] is True

    account.log_on()
    state = account.describe_state()
    assert state["num_logons"] is 1
    assert state["num_logoffs"] is 0
    assert state["num_group_changes"] is 0
    assert state["username"] is "Jake"
    assert state["password"] is "totally_hashed_password"
    assert state["account_type"] is AccountType.USER.value
    assert state["enabled"] is True

    account.log_off()
    state = account.describe_state()
    assert state["num_logons"] is 1
    assert state["num_logoffs"] is 1
    assert state["num_group_changes"] is 0
    assert state["username"] is "Jake"
    assert state["password"] is "totally_hashed_password"
    assert state["account_type"] is AccountType.USER.value
    assert state["enabled"] is True

    account.disable()
    state = account.describe_state()
    assert state["num_logons"] is 1
    assert state["num_logoffs"] is 1
    assert state["num_group_changes"] is 0
    assert state["username"] is "Jake"
    assert state["password"] is "totally_hashed_password"
    assert state["account_type"] is AccountType.USER.value
    assert state["enabled"] is False
