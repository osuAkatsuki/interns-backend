import pytest_mock

from app import commands
from testing import sample_data


async def test_echo_handler_should_echo_args():
    # arrange
    osu_session = sample_data.fake_osu_session()

    # act
    command_response = await commands.roll_handler(osu_session, ["42"])

    # assert
    assert command_response is not None
    assert command_response in range(0, 100)


async def test_roll_handler_should_roll_between_default_range():
    # arrange
    session = sample_data.fake_osu_session()

    # act
    command_response = await commands.roll_handler(session, ["100"])

    # assert
    assert command_response is not None
    assert 0 <= int(command_response) < 100


async def test_block_handler_should_block_user(mocker: pytest_mock.MockerFixture):
    # arrange
    fake_session = sample_data.fake_osu_session()
    fake_account = sample_data.fake_account()

    mocker.patch(
        "app.repositories.accounts.fetch_by_username",
        return_value=fake_account,
    )
    mocker.patch(
        "app.repositories.relationships.fetch_all",
        return_value=[],
    )
    mocker.patch(
        "app.repositories.relationships.create",
        return_value={
            "account_id": fake_session["account_id"],
            "target_id": fake_account["account_id"],
            "relationship": "blocked",
        },
    )

    # act
    command_response = await commands.block_handler(
        fake_session, [fake_account["username"]]
    )

    # assert
    assert command_response is not None
    assert (
        command_response
        == f"{fake_session['username']} successfully blocked {fake_account['username']}"
    )


async def test_block_handler_should_not_block_user_if_not_found(
    mocker: pytest_mock.MockerFixture,
):
    # arrange
    fake_session = sample_data.fake_osu_session()
    fake_account = sample_data.fake_account()

    mocker.patch(
        "app.repositories.accounts.fetch_by_username",
        return_value=None,
    )

    # act
    command_response = await commands.block_handler(
        fake_session, [fake_account["username"]]
    )

    # assert
    assert command_response is not None
    assert command_response == f"{fake_account['username']} could not be blocked"


async def test_block_handler_should_not_block_user_if_already_blocked(
    mocker: pytest_mock.MockerFixture,
):
    # arrange
    fake_session = sample_data.fake_osu_session()
    fake_account = sample_data.fake_account()

    mocker.patch(
        "app.repositories.accounts.fetch_by_username",
        return_value=fake_account,
    )
    mocker.patch(
        "app.repositories.relationships.fetch_all",
        return_value=[
            {
                "account_id": fake_session["account_id"],
                "target_id": fake_account["account_id"],
                "relationship": "blocked",
            }
        ],
    )

    # act
    command_response = await commands.block_handler(
        fake_session, [fake_account["username"]]
    )

    # assert
    assert command_response is not None
    assert command_response == f"{fake_account['username']} is already blocked"
