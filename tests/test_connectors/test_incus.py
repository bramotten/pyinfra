import shlex
from subprocess import PIPE
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from pyinfra.api import Config, State
from pyinfra.api.connect import connect_all
from pyinfra.api.exceptions import InventoryError, PyinfraError
from pyinfra.connectors.util import make_unix_command

from ..util import make_inventory

def make_raise_exception_function(cls, *args, **kwargs):
    def handler(*a, **kw):
        raise cls(*args, **kwargs)
    return handler


class TestSSHConnector(TestCase):
    def setUp(self):
        pass
        # self.fake_connect_patch = mock.patch("pyinfra.connectors.ssh.SSHClient.connect")
        # self.fake_connect_mock = self.fake_connect_patch.start()

    def tearDown(self):
        pass
        # self.fake_connect_patch.stop()

    def test_connect_all(self):
        inventory = make_inventory(hosts=("@incus/somehost", "@incus/anotherhost",))
        state = State(inventory, Config())
        connect_all(state)
        assert len(state.active_hosts) == 2




# # @patch("pyinfra.connectors.incus.local.shell", fake_docker_shell)
# # @patch("pyinfra.connectors.incus.mkstemp", lambda: (None, "__tempfile__"))
# # @patch("pyinfra.connectors.incus.os.remove", lambda f: None)
# # @patch("pyinfra.connectors.incus.os.close", lambda f: None)
# # @patch("pyinfra.connectors.incus.open", mock_open(read_data="test!"), create=True)
# # @patch("pyinfra.api.util.open", mock_open(read_data="test!"), create=True)
# class TestIncusConnector(TestCase):
#     def setUp(self):
#         # print("NOTE: this incus stuff might do nothing. \
#         #     Leaving it in case I want to copy more from Docker.")
#         self.fake_popen_patch = patch("pyinfra.connectors.util.Popen")
#         self.fake_popen_mock = self.fake_popen_patch.start()

#     def tearDown(self):
#         self.fake_popen_patch.stop()

#     def test_missing_image(self):
#         with self.assertRaises(InventoryError):
#             make_inventory(hosts=("@incus",))

#     def test_run_shell_command(self):
#         inventory = make_inventory(hosts=("@incus/a",))
#         State(inventory, Config())

#         command = "touch /root/iEXIST"
#         self.fake_popen_mock().returncode = 0

#         host = inventory.get_host("@incus/a")
#         host.connect()
#         out = host.run_shell_command(
#             command,
#             _stdin="hello",
#             _get_pty=True,
#             print_output=True,
#         )
#         assert len(out) == 2
#         assert out[0] is True

#         # command = make_unix_command(command).get_raw_value()
#         # command = shlex.quote(command)
#         # docker_command = "docker exec -it containerid sh -c {0}".format(command)
#         # shell_command = make_unix_command(docker_command).get_raw_value()

#         # self.fake_popen_mock.assert_called_with(
#         #     shell_command,
#         #     shell=True,
#         #     stdout=PIPE,
#         #     stderr=PIPE,
#         #     stdin=PIPE,
#         # )
