#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import click


from .commands.helpers import cfg
from .commands.sandbox import sandbox
from .commands.service import service
from .commands.skill import skill


@click.group()
def entry_point():
    """wa-cli allows you to

    \b
    * create individual developer sandboxes for Watson Assistant skills
    * decompose skill JSON files into diff friendly XML and CSV files
    * clone the skills from a service to another service
    * run k-fold tests on a skill file
    * download, deploy and delete skills
    """
    pass


@entry_point.command()
@click.option('--main-branch', default='master', show_default=True)
@click.option('--no-prompt', default=False, is_flag=True)
def init(main_branch, no_prompt):
    """
    Initialise the current folder for further work with wa-cli
    """
    cfg.init(not no_prompt, main_branch)


@entry_point.command()
def env():
    """
    Instructions to set env vars and enable command completion
    """
    cfg.env_help()


@entry_point.command()
def travis():
    """
    Add a .travis.yml file to run dialog flow tests
    """
    cfg.travis()


entry_point.add_command(sandbox)
entry_point.add_command(service)
entry_point.add_command(skill)

if __name__ == "__main__":
    entry_point()
