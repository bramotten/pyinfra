"""
Facts about Incus instances (sometime: sockets).
"""

from __future__ import annotations
import json
from typing_extensions import override
from typing import TypedDict

from pyinfra.api import FactBase

# TODO: IncusListType = TypedDict...
# I have no clue

class IncusList(FactBase):

    default = list

    @override
    def command(self, running=True) -> str:
        return 'incus list --format=json'

    @override
    def process(self, output) -> list:
        output = "".join(output)
        return json.loads(output)

class IncusRunning(IncusList):

    @override
    def process(self, output):
        infolist = super().process(output)
        return list(filter(lambda info: info['status'] == 'Running', infolist))
