# DB-ify
Decorate functions to write their outputs and given parameters to a MySQL database. 

## Installation / Set-up

First, navigate to the root folder of this repo, and activate the virtual environment you would like to install in. Then install dbify:
```
pip install -e .
```

In order to use `dbify`, you will need a MySQL server set up.

## Usage

This library provides a decorator, `dbify`, that modifies the function it decorates to store its output to a MySQL database, along with each of the function's given parameters. The function must return a dictionary mapping column names to the values that will be stored in the database.

_Note that MySQL database is limited in the types of objects it can store. Right now all return values and arguments to db-ified functions must be of type `int`, `float`, `str`, `bool`, or `None`._

Consider the following example:
```python
from dbify import dbify

@dbify('test_database', 'test_table')
def example(a, b, c=0):
    return {
        'x': a + b + c,
        'y': a * b * c,
        'z': a > b
    }
    
example(2, 3, 2)
```

In this example we assume that there is a database named `'test_database'`. Within this database, we will insert into a table called `'test_table'`, which will be created if it doesn't exist. We also assume that the user has set up a configuration file for connecting to their MySQL server (see more on this below). Executing this code will result in adding the following row to `'test_table'`:

```
id           | modified        | a | b | c | x | y  | z
-------------+-----------------+---+---+---+---+----+------
<unique id>  | <date/time run> | 2 | 3 | 1 | 7 | 12 | False
```

### Connecting to a MySQL server

The `dbify` decorator uses an instance of `dbify.connections.DbServer` in order to connect to a MySQL server. A `DbServer` object keeps track of the host name, port, user credentials, etc., required to connect to the database server. There are two options for connecting: (1) directly by host name, and (2) via SSH tunneling. Use the former if your server is accessible over the internet or running on the same machine your code is running on; use the latter if you have a local MySQL server running on another machine that you would like to connect to via SSH.

To connect to the server using method (1), the example code above could read as follows:
```python
from dbify import dbify
from dbify.connections import DbServer

@dbify(
    'test_database', 
    'test_table',
    db_server=DbServer(
        db_name='test_database',
        db_user='root',
        db_password='password',
        db_host='127.0.0.1',
        db_port=3306))
def example(a, b, c=0):
    return {
        'x': a + b + c,
        'y': a * b * c,
        'z': a > b
    }
    
example(2, 3, 2)
```

To connect to the server using method (2), the example code above could read as follows:
```python
@dbify(
    'test_database', 
    'test_table',
    db_server=DbServer(
        db_name='test_database',
        db_user='root',
        db_password='password',
        db_host='127.0.0.1',
        db_port=3306,
        ssh_address='name-of-remote-server.com',
        ssh_user='user',
        ssh_keyfile='~/.ssh/keyfile',
        local_bind_host='0.0.0.0',
        local_bind_port=3307))
def example(a, b, c=0):
    return {
        'x': a + b + c,
        'y': a * b * c,
        'z': a > b
    }
    
example(2, 3, 2)
```

The easiest way to connect to a MySQL database server is using a configuration file. By creating a configuration file, you can avoid using an instance of `DbServer` directly. To create a configuration file, create a file called `~/.dbify_config`, and include in it the parameters passed to the `DbServer` constructor above, e.g., to connect using method (1), the contents of `~/.dbify_config` could be:
```
db_user = root
db_password = password
db_host = 127.0.0.1
db_port = 3306
```

### Tip on viewing your databases

To view your databases on Mac OS, you can use sequel pro. If using a modern version of MySQL, you may need the nightly version.
```
brew cask install homebrew/cask-versions/sequel-pro-nightly
```
