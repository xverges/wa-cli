#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys

import click
from .helpers import protect_readonly
from .helpers import common_options
from .helpers import cfg
from .wa import wa
from .wa_testing import wa_testing
from .workbench import workbench


@click.group()
@click.pass_context
def skill(ctx):
    """
    Skill related commands
    """
    cfg.check_context(ctx)


@skill.command(name="list")
@common_options.add(common_options.mandatory)
@click.argument('pattern', default='*')
def list_skills(apikey, url, pattern):
    """
    List skills matching 'pattern' by name
    """
    skills = wa.list_skills(apikey, url, pattern)
    for skill in skills:
        click.echo(f'{skill.updated_on}   {skill.id}   {skill.name}')


@skill.command()
@click.pass_context
@common_options.add(common_options.mandatory)
@click.argument('skill_file', type=click.Path(exists=True))
@click.option('--force', is_flag=True)
@protect_readonly
def deploy(ctx, apikey, url, skill_file, force):
    """
    Create/update a skill from a json file
    """
    success = wa.deploy_skill(apikey, url, skill_file, force)
    click.echo(f'Success: {success}')


@skill.command(name="delete")
@common_options.add(common_options.mandatory)
@click.argument('skill_id', required=True)
@protect_readonly
def delete_skill(apikey, url, skill_id):
    """
    Delete a skill
    """
    success = wa.delete_skill(apikey, url, skill_id)
    click.echo(f'Success: {success}')


@skill.command()
@click.pass_context
@click.argument('skill_file', type=click.Path(exists=True))
def decompose(ctx, skill_file):
    """
    Decompose a json skill file with WAW (Watson Assistant Workbench)
    """
    success = workbench.decompose_skill_file(skill_file)
    click.echo(f'Success: {success}')


@skill.command()
@click.pass_context
@click.argument('skill_name', type=click.STRING, required=True)
@click.argument('new_name', type=click.STRING, required=False)
@click.option('--force', is_flag=True)
def assemble(ctx, skill_name, new_name, force):
    """
    Re-assemble WAW-files into a json skill file
    """
    success = workbench.reassemble_skill_file(skill_name, new_name, force)
    click.echo(f'Success: {success}')


@skill.command()
@click.pass_context
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
def get(ctx, apikey, url, skill_name):
    """
    Download a skill to the skills folder
    """
    skill_file = wa.get_skill(apikey, url, skill_name)
    if skill_file:
        click.echo(f'Downloaded to: {skill_file}')
    else:
        click.echo('Command failed')


@click.group()
def test():
    """
    Test related commands
    """


@test.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_file', type=click.Path(exists=True))
@click.option('--folds', default=5, show_default=True)
@click.option('--show-graphics', is_flag=True, help='Open a browser with the generated images')
def kfold(apikey, url, skill_file, folds, show_graphics):
    """
    k-fold test to measure ground truth consistency

    \b
    See https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/kfold.md for details
    """
    wa_testing.k_fold(apikey, url, skill_file, folds, show_graphics)


@test.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
@click.option('--show-graphics', is_flag=True, help='Open a browser with the generated images')
def blind(apikey, url, skill_name, show_graphics):
    """
    blind test using a CSV file with utterances and expected intents

    \b
    The file <project_root>/test/blind/<skill_name>/input.csv will be used as input.
    See https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/blind.md for details
    """
    wa_testing.blind(apikey, url, skill_name, show_graphics)


@test.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
def flow(apikey, url, skill_name):
    """
    dialog flow test

    \b
    Files matching <project_root>/test/flow/<skill_name>/*.tsv will be used as input. Example input:
    https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/dialog_test/tests/Customer_Care_Test.tsv
    You can start an new conversation specifying NEWCONVERSATION as the user input.
    """
    rc = wa_testing.flow(apikey, url, skill_name)
    if rc:
        sys.exit(rc)


skill.add_command(test)


# def router(target):
