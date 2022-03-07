from pipeline.validate import FieldMeta
from pipeline.validators.uka import validate_uka

import pytest

@pytest.fixture
def uka_validator():
    return validate_uka

def pytest_configure():
    pytest.field_meta = FieldMeta