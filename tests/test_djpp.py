from djpp import pyproject
from os import path


def test_load():
    data = pyproject.load_all(path.join(path.dirname(path.dirname(path.abspath(__file__)))), 'pyproject.toml')
    assert data['tool']['poetry']['name'] == 'django-pyproject'
