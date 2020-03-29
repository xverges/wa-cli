#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import click


from .commands.sandbox import sandbox
from .commands.service import service
from .commands.skill import skill


@click.group()
def entry_point():
    """Create individual developer sandboxes for Watson Assistant skills"""
    pass


@entry_point.command()
def init():
    """
    Initialise the current folder for further work with wa-cli
    """
    from .commands.helpers.cfg import init
    init()


entry_point.add_command(sandbox)
entry_point.add_command(service)
entry_point.add_command(skill)

if __name__ == "__main__":
    entry_point()
