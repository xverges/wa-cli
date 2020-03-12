#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import click
from .helpers import protect_readonly
from .helpers import common_options
from .wa import wa


@click.group()
def skills():
    """
    Skill related commands
    """
    pass


@skills.command(name="list")
@common_options.add(common_options.mandatory)
@click.argument('pattern', default='*')
def list_skills(apikey, url, pattern):
    """
    List skills matching 'pattern' by name
    """
    skills = wa.list_skills(apikey, url, pattern)
    for skill in skills:
        click.echo(f'{skill.id} {skill.name}')


@skills.command(name="delete")
@common_options.add(common_options.mandatory)
@click.argument('skill_id', required=True)
@protect_readonly
def delete_skill(apikey, url, skill_id):
    """
    Delete a skill
    """
    success = wa.delete_skill(apikey, url, skill_id)
    click.echo(f'Success: {success}')

# def router(target):
