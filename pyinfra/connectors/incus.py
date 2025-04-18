from __future__ import annotations

import json
import os
from tempfile import mkstemp
from typing import TYPE_CHECKING, Tuple

import click
from typing_extensions import TypedDict, Unpack, override

from pyinfra import local, logger
from pyinfra.api import QuoteString, StringCommand
from pyinfra.api.exceptions import ConnectError, InventoryError, PyinfraError
from pyinfra.api.util import get_file_io
from pyinfra.progress import progress_spinner

from .base import BaseConnector, DataMeta
from .local import LocalConnector
from .util import CommandOutput, extract_control_arguments, make_unix_command_for_host

class ConnectorData(TypedDict):
    incus_instance: str

connector_data_meta: dict[str, DataMeta] = {
    "incus_instance": DataMeta("Instance ID, as in: incus <cmd> [<remote>:]<instance>"),
}

def _local_shell(cmd):
    return local.shell(cmd)

def _find_start_docker_container(container_id) -> tuple[str, bool]:
    docker_info = local.shell("docker container inspect {0}".format(container_id))
    assert isinstance(docker_info, str)
    docker_info = json.loads(docker_info)[0]
    if docker_info["State"]["Running"] is False:
        logger.info("Starting stopped container: {0}".format(container_id))
        local.shell("docker container start {0}".format(container_id))
        return container_id, False
    return container_id, True


class IncusConnector(BaseConnector):
    __examples_doc__ = """
    work in progress
    """
    handles_execution = True

    data_cls = ConnectorData
    data_meta = connector_data_meta
    data: ConnectorData

    local: LocalConnector
    # NOTE: I copied all this local stuff from ./docker.py
    # Maybe ./util.py would have been better

    incus_instance: str
    latest_info: str = ""

    def __init__(self, state: "State", host: "Host"):
        super().__init__(state, host)
        self.local = LocalConnector(state, host)

    @staticmethod
    def make_names_data(name=None):
        if not name:
            raise InventoryError(f"no Incus instance ID provided: {name=}")
        yield (
            f"@incus/{name}",
            {"incus_instance": name},
            ["@incus"],
        )

    @override
    def connect(self) -> None:
        logger.debug(f"Welcome")
        # self.local.connect()

        self.incus_instance = self.data["incus_instance"]
        with progress_spinner({f"obtainining Incus info for: {self.incus_instance}"}):
            try:
                self.info = local.shell(f"incus info {self.incus_instance}")
                # TODO: try run_local_process
                """
                if print_input:
                    click.echo("{0}>>> {1}".format(self.host.print_prefix, rsync_command), err=True)

                return_code, output = run_local_process(
                    rsync_command,
                    print_output=print_output,
                    print_prefix=self.host.print_prefix,
                )
                """
            except BaseException as err:
                raise ConnectError(f"{err}")

    def run_shell_command(
        self,
        command: StringCommand,
        print_output: bool = False,
        print_input: bool = False,
        **arguments: Unpack["ConnectorArguments"],
    ) -> Tuple[bool, CommandOutput]:
        local_arguments = extract_control_arguments(arguments)

        command = make_unix_command_for_host(self.state, self.host, command, **arguments)

        incus_flags = "-t" if local_arguments.get("_get_pty") else "-T"
        incus_command = StringCommand(
            "incus",
            "exec",
            incus_flags,
            self.incus_instance,
            "--",
            command,
        )

        return self.local.run_shell_command(
            incus_command,
            print_output=print_output,
            print_input=print_input,
            **local_arguments,
        )

    @override
    def put_file(
        self,
        filename_or_io,
        remote_filename,
        remote_temp_filename=None,  # ignored
        print_output: bool = False,
        print_input: bool = False,
        **arguments,
    ) -> bool:
        fd, temp_filename = mkstemp()

        try:
            # Load our file or IO object and write it to the temporary file
            with get_file_io(filename_or_io) as file_io:
                with open(temp_filename, "wb") as temp_f:
                    data = file_io.read()

                    if isinstance(data, str):
                        data = data.encode()

                    temp_f.write(data)

            incus_command = StringCommand(
                "incus",
                "file",
                "push",
                temp_filename,
                f"{self.incus_instance}/{remote_filename}",
            )

            status, output = self.local.run_shell_command(
                incus_command,
                print_output=print_output,
                print_input=print_input,
            )
        finally:
            os.close(fd)
            os.remove(temp_filename)

        if not status:
            raise IOError(output.stderr)

        if print_output:
            click.echo(
                "{0}file uploaded to Incus instance: {1}".format(
                    self.host.print_prefix,
                    remote_filename,
                ),
                err=True,
            )

        return status

    @override
    def get_file(
        self,
        remote_filename,
        filename_or_io,
        remote_temp_filename=None,  # ignored
        print_output=False,
        print_input=False,
        **kwargs,  # ignored (sudo/etc)
    ) -> bool:
        fd, temp_filename = mkstemp()
        try:
            incus_command = StringCommand(
                "incus",
                "file",
                "pull" f"{self.container_id}/{remote_filename}",
                temp_filename,
            )

            status, output = self.local.run_shell_command(
                incus_command,
                print_output=print_output,
                print_input=print_input,
            )

            # Load the temporary file and write it to our file or IO object
            with open(temp_filename, "rb") as temp_f:
                with get_file_io(filename_or_io, "wb") as file_io:
                    data = temp_f.read()
                    file_io.write(data)
        finally:
            os.close(fd)
            os.remove(temp_filename)

        if not status:
            raise IOError(output.stderr)

        if print_output:
            click.echo(
                "{0}file downloaded from Incus instance: {1}".format(
                    self.host.print_prefix,
                    remote_filename,
                ),
                err=True,
            )

        return status
