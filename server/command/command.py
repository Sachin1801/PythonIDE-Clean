#!/usr/bin/env python3

from .ide_cmd import IdeCmd


class Command(IdeCmd):
    def __init__(self) -> None:
        super(Command, self).__init__()
