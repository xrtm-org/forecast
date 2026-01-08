import pytest


def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", default=False, help="run live tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "live: mark test as live to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        # --run-live given in cli: do not skip live tests
        return
    skip_live = pytest.mark.skip(reason="need --run-live option to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
