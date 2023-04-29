def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    import email_validator

    email_validator.TEST_ENVIRONMENT = True
