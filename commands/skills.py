#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import click
from .helpers import protect_readonly
from .helpers import common_options
from .helpers import cfg
from .wa import wa
from .workbench import workbench


@click.group()
@click.pass_context
def skills(ctx):
    """
    Skill related commands
    """
    cfg.check_context(ctx)


@skills.command(name="list")
@common_options.add(common_options.mandatory)
@click.argument('pattern', default='*')
def list_skills(apikey, url, pattern):
    """
    List skills matching 'pattern' by name
    """
    skills = wa.list_skills(apikey, url, pattern)
    for skill in skills:
        click.echo(f'{skill.updated_on}   {skill.id}   {skill.name}')


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


@skills.command()
@click.pass_context
@click.argument('skill_file', type=click.Path(exists=True))
def decompose(ctx, skill_file):
    """
    Decompose a json skill file with WAW (Watson Assistant Workbench)
    """
    success = workbench.decompose_skill_file(skill_file)
    click.echo(f'Success: {success}')


# def router(target):
