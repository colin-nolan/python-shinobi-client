[![Build Status](https://travis-ci.com/colin-nolan/python-shinobi-client.svg?branch=master)](https://travis-ci.com/colin-nolan/python-shinobi-client)
[![Code Coverage](https://codecov.io/gh/colin-nolan/python-shinobi-client/branch/master/graph/badge.svg)](https://codecov.io/gh/colin-nolan/python-shinobi-client)

# Shinobi Python Client
_A Python client for controlling [Shinobi](https://gitlab.com/Shinobi-Systems/Shinobi) (an open-source video management 
solution)._


## About
This package contains an (very incomplete) set of tools for interacting with Shinobi using Python.

This library tries to use the (rather unique) [documented API](https://shinobi.video/docs/api) but it also uses 
undocumented endpoints (which may not be stable).


## Installation
Install from [PyPi](https://pypi.org/project/shinobi-client/):
```bash
pip install shinobi-client
```

Install with ability to start a Shinobi installation:
```bash
pip install shinobi-client[shinobi-controller]
```

Install with CLI:
```bash
pip install shinobi-client[cli]
```

## Usage
### Python
Start with creating the client for a particular Shinobi installation:
```python
from shinobi_client import ShinobiClient

shinobi_client = ShinobiClient(host, port, super_user_token)
```

#### User
```python
user = shinobi_client.user.get(email)

users = shinobi_client.user.get_all()

user = shinobi_client.user.create(email, password)

modified = shinobi_client.user.modify(email, password=new_password)

deleted = shinobi_client.user.delete(email)
```

#### API Key
```python
api_key = shinobi_client.api_key.get(email, password)
```

#### Shinobi Controller
Starts/Stops a temporary [containerised installation of Shinboi](https://github.com/colin-nolan/docker-shinobi). Written
for the purpose of testing but it is also installable as an extra. Requires Docker.
```python
from shinobi_client import start_shinobi

with start_shinobi() as shinobi_client:
    print(shinobi_client.url)
    # Do things with a temporary Shinobi installation
```
or
```python
from shinobi_client import ShinobiController

controller = ShinobiController()
shinobi_client = controller.start()
print(shinobi_client.url)
# Do things with a temporary Shinobi installation
controller.stop()
```

### CLI
A basic auto-generated CLI is available if the package is installed with the `cli` extra: 
```bash
PYTHONPATH=. python shinobi_client/user.py \
        --host=HOST --port=PORT --super_user_token=SUPER_USER_TOKEN \
    get user@example.com
```
e.g.
```bash
$ PYTHONPATH=. python shinobi_client/cli.py \
        --host='0.0.0.0' --port=50694 --super_user_token='26dd3352-73c4-4bbd-8b09-17f2aacbd7b9' \
    create 'user@example.com' 'password123'
```


## Development
Install with dev-dependencies:
```bash
poetry install --no-root --extras "shinobi-controller, cli"
```

Run tests with:
```bash
python -m unittest discover -v -s shinobi/tests
```


## Legal
[AGPL v3.0](LICENSE.txt). Copyright 2020 Colin Nolan.

I am not affiliated to the development of Shinobi project in any way. This work is in no way related to the company that
I work for.
