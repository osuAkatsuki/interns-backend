from unittest.mock import create_autospec

import pytest_mock

from server import clients
from server.adapters.database import Database
from server.repositories import accounts
from testing import sample_data


async def test_should_create_account(
    mocker: pytest_mock.MockerFixture,
):
    # arrange
    fake_account = sample_data.fake_account()
    clients.database = create_autospec(Database)
    mocker.patch(
        "server.clients.database.fetch_one",
        return_value={
            "account_id": fake_account["account_id"],
            "username": fake_account["username"],
            "email_address": fake_account["email_address"],
            "privileges": fake_account["privileges"],
            "password": fake_account["password"],
            "country": fake_account["country"],
            "created_at": fake_account["created_at"],
            "updated_at": fake_account["updated_at"],
        },
    )

    # act
    account = await accounts.create(
        account_id=fake_account["account_id"],
        username=fake_account["username"],
        email_address=fake_account["email_address"],
        privileges=fake_account["privileges"],
        password=fake_account["password"],
        country=fake_account["country"],
    )

    # assert
    assert account == fake_account
