[![Build Status](https://travis-ci.com/colin-nolan/python-shinobi.svg?branch=master)](https://travis-ci.com/colin-nolan/python-shinobi)
[![Code Coverage](https://codecov.io/gh/colin-nolan/python-shinobi/branch/master/graph/badge.svg)](https://codecov.io/gh/colin-nolan/python-shinobi)

# Shinobi Python Client
_A Python client for controlling [Shinobi](https://gitlab.com/Shinobi-Systems/Shinobi), an open-source video management 
solution._

## Installation
TODO

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
TODO


## Legal
[AGPL v3.0](LICENSE.txt). Copyright 2020 Colin Nolan.

I am not affiliated to the development of Shinobi project in any way.
