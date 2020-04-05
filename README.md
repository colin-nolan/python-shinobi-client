[![Build Status](https://travis-ci.com/colin-nolan/python-shinobi.svg?branch=master)](https://travis-ci.com/colin-nolan/python-shinobi)
[![Code Coverage](https://codecov.io/gh/colin-nolan/python-shinobi/branch/master/graph/badge.svg)](https://codecov.io/gh/colin-nolan/python-shinobi)

# Shinobi Python Client
_A Python client for controlling [Shinobi](https://gitlab.com/Shinobi-Systems/Shinobi), an open-source video management 
solution._


## About
This package contains an (very incomplete) set of tools for interacting with Shinobi using Python.

This library tries to use the (rather unique) [documented API](https://shinobi.video/docs/api) but it also uses 
undocumented endpoints (which may not be stable).


## Installation
Install from [PyPi](https://pypi.org/project/shinobi-client/):
```
pip install shinobi-client
```

Install with ability to start a Shinobi installation:
```
pip install shinobi-client[shinobi-controller]
```


## Usage
### User ORM
```python
from shinobi_client import ShinobiUserOrm

user_orm = ShinobiUserOrm(host, port, super_user_token)

user = user_orm.get(email)

users = user_orm.get_all()

user = user_orm.create(email, password)

modified = user_orm.modify(email, password=new_password)

deleted = user_orm.delete(email)
```

### Shinobi Controller
Starts/Stops a temporary [containerised installation of Shinboi](https://github.com/colin-nolan/docker-shinobi). Written
for the purpose of testing but it is installable as an extra.
```python
from shinobi_client import start_shinobi

with start_shinobi() as shinobi:
    print(shinobi.url)
    # Do things with a temporary Shinobi installation
```
or
```python
from shinobi_client import ShinobiController

controller = ShinobiController()
shinobi = controller.start()
print(shinobi.url)
# Do things with a temporary Shinobi installation
controller.stop()
```


## Development
Install with dev-dependencies:
```
poetry install --no-root --extras "shinobi-controller"
```

Run tests with:
```
python -m unittest discover -v -s shinobi/tests
```


## Legal
[AGPL v3.0](LICENSE.txt). Copyright 2020 Colin Nolan.

I am not affiliated to the development of Shinobi project in any way. This work is in no way related to the company that
I work for.
