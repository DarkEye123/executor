# Executor
The Executor is an idea of an *unified API* for all models possibly used
in the future as a remote execution layer. Therefore, the Executor is an
abstraction of above the implemented model. 

The Executor provides necessary API without an actual
implementation. Whole implementation is provided by an integrated
model, included via encapsulation into the Executor. Therefore, the
Executor serves as a **facade**. 

This module is used directly by the engineer or by an another
abstraction layer. The Executor can be initialised only once, therefore, it is also a *singleton*

So why use Executor? Executor was developed as part of my thesis. Also, it is a living
module used by Red Hat Middleware Messaging team. It was customized for team needs, but with
mopdularity in mind. This repository provides only the necessary parts, which I was able 
upload without breaking any license agreements.

Executor in a sense provides very similar functionality for simultaneous remote execution as [Ansible.](https://github.com/ansible/ansible])<br>
But it is not meant to be an automation system. It just serves as a *pythonic* remote execution solution.

## Dependencies:
  * pytest-timeout
  * pytest-capturelog
  * mock
  * pytest
  * paramiko

## Models and Executor
Model could be defined as a class containing all methods and attributes
necessary to create connection, store data, manipulate streams and
communicate with rest of the classes. It also provides abstraction for a
concrete module used as a remote execution provider. By the remote
execution provider is meant e.g. paramiko or an other similar solution.

![Instantiation example](https://s26.postimg.org/jm79082jt/executor_mapping.png)

## Unit Tests
To execute them:<br>`./unittests/run.sh`<br>


##### Or try:
`py.test -v *.py */*.py`

*NOTE*<br>
In case of problems, be sure you are in the directory with unittests


## EXAMPLE
Here is working example which does not need a dtests to run
Make sure you are in the *correct* directory.
Also, **edit** 'username' and 'password' in the code sample.

```python
import argparse
import logging

from executor import Executor
from networkobjects.host import Host
from networkobjects.user import User

executor = Executor()
local_hosts = ["127.0.0.1", "localhost"]


def test_echo_executor_localhost(username="fill_me", password="fill_me"):
    """ Test echo client """
    for host_name in local_hosts:
        host = Host(address=host_name)
        user = User(username=username, password=password)
        data = "test string"
        executor.create_connection(host=host, user=user)
        executor.connect()
        cmd = executor.create_command("echo %s" % data)
        result = executor.execute(command=cmd)
        result.wait_for_data()
        logging.info("stdout: %s" % result.stdout)
        logging.info("stderr: %s" % result.stderr)
        logging.info("ecode: %s" % result.ecode)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', dest='username', required=False, default="root", type=str, metavar='str',
                        help="username for your remote node")
    parser.add_argument('-p', '--password', dest='password', required=True, default=None, type=str, metavar='str',
                        help="password for your remote node")
    args = parser.parse_args()
    test_echo_executor_localhost(username=args.username, password=args.password)
```
