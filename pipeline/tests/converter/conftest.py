import pytest

from pipeline.convert import ModsParser


@pytest.fixture
def parser():
    return ModsParser()
