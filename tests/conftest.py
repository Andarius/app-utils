from pathlib import Path
import pytest
import shutil
import os

DATA_FOLDER = Path(__file__).parent / 'data'
TMP_FILES_FOLDER = Path(__file__).parent / 'tmp'


@pytest.fixture(scope='function')
def tmp_folder():
    if TMP_FILES_FOLDER.exists():
        shutil.rmtree(TMP_FILES_FOLDER)

    TMP_FILES_FOLDER.mkdir()

    yield TMP_FILES_FOLDER

    shutil.rmtree(TMP_FILES_FOLDER)


@pytest.fixture(scope='function')
def project_path(tmp_folder):
    path = tmp_folder / 'my-project'
    shutil.copytree(DATA_FOLDER / 'my-project', path)
    yield path
