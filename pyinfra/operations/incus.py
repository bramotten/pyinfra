"Manage Incus instances. Not Incus itself."

from __future__ import annotations

from typing import Any
import json
from pathlib import Path
import shlex

from pyinfra import host
from pyinfra.api import operation
from pyinfra.facts.incus import IncusList

def str2list(s):
    return s.split(',')

def str2pairs(s):
    return [x.split(':') for x in str2list(s)]

def dashedpath(p):
    return str(p).replace('-', '--').replace('/', '-')

@operation()
def instance(
    name: str,
    image="images:alpine/edge",
    mountmap: list[tuple[str | Path,  str | Path]]=[],
    networks=[], # TODO
    portmap={}, # TODO
    clean_mountmap=False,
    clean_networks=False,
    clean_portmap=False,
    present=True,
):
    """

    mountmap:
        - creates a device to map *into* the instance
        - likes list of ``(src, dst)`` pairs
        - ``dst`` must be absolute (will attempt ``src`` via working dir)
        - usage via CLI: ... mountmap="./examples:/root/examples,..."

    portmap:
        - TODO
        - https://linuxcontainers.org/incus/docs/main/howto/network_forwards

    clean:
        -
    """
    incuslist = host.get_fact(IncusList)
    info = next(filter(lambda x: x['name'] == name, incuslist), None)

    # Container exists and we don't want it
    if not present:
        if info:
            yield "incus delete --force {0}".format(name)
        else:
            host.noop("{0} already did not exists".format(name))
        return # fine?

    # Container doesn't exist and we want it
    if present:
        if info:
            host.noop("{0} already existed".format(name))
        else:
            # Command to create the container:
            yield f"incus launch {image} {name} < /dev/null"

    # Does this work for remotes?
    # incus file mount <instance_name>/<path_to_directory> <local_location>
    # incus file mount <instance_name> [--listen <address>:<port>]
    if mountmap:
        if isinstance(mountmap, str):
            mountmap = str2pairs(mountmap)
            assert all(len(x) == 2 for x in mountmap)

        # TODO: get current, to skip and clean

        for src, dst in mountmap:
            mapname = dashedpath(src) + '.INTO.' + dashedpath(dst)
            while mapname.startswith('-'): mapname = mapname[1:]
            print(mapname)

            # If not taken:
            thus = f"source={Path(src).absolute()} path={dst}"
            yield f"incus config device add {name} {mapname} disk {thus}"
