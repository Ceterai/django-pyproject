from djpp import pyproject
from os import path as p


def test_load():
    path = p.join(p.dirname(p.dirname(p.abspath(__file__))), 'pyproject.toml')
    data = pyproject.load_all(path)
    assert data['tool']['poetry']['name'] == 'django-pyproject'
