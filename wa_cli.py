#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import click


from commands.sandbox import sandbox
from commands.service import service
from commands.skills import skills


@click.group()
def entry_point():
    pass


@entry_point.command()
def init():
    """
    Initialise the current folder for further work with wa-cli
    """
    from commands.helpers.cfg import init
    click.confirm('This will initialise the current folder as a wa-cli project. Continue?',
                  abort=True,
                  default=True)
    apikey = click.prompt('Enter the apikey of the service that you are going to be targeting', '')
    url = click.prompt('Enter the url of the service that you are going to be targeting', '')
    apikey_src = click.prompt('If you plan to clone skills from a different service, enter its apikey', '')
    url_src = click.prompt('If you plan to clone skills from a different service, enter its url', '')
    main_branch = click.prompt('Enter your main branch. Usually, "master"', 'master')
    init(apikey, url, apikey_src, url_src, main_branch)
    click.echo('These values have been added to a .env file')
    click.echo('You can set them as environment variables running \n'
               '   set -o allexport; source .env; set +o allexport')


entry_point.add_command(sandbox)
entry_point.add_command(service)
entry_point.add_command(skills)

if __name__ == "__main__":
    entry_point()
