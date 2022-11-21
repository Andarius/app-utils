import shutil
from pathlib import Path

import pytest

DATA_FOLDER = Path(__file__).parent / 'data'


@pytest.fixture(scope='function')
def project_path(tmp_path):
    path = tmp_path / 'myApp'
    shutil.copytree(DATA_FOLDER / 'myApp', path)
    yield path

@pytest.fixture
def static_folder():
    return DATA_FOLDER
