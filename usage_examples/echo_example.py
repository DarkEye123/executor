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
