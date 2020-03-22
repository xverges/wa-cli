#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import os
import sys

import click
from .helpers import protect_readonly
from .helpers import common_options
from .helpers import cfg
from .helpers import git
from .wa import wa
from .workbench import workbench


@click.group()
@click.pass_context
def sandbox(ctx):
    """
    Work with skills in a branch-dependant sandbox

    \b
    $ git checkout master
    $ wa-cli sandbox init your_skill
    $ git checkout -b topic_branch
    $ wa-cli sandbox push your_skill
    # Go to the WA GUI and work with topic_branch__your_skill
    $ wa_cli sandbox pull
    $ git diff
    # ...
    """
    cfg.check_context(ctx)


@sandbox.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True, metavar='<skill_name>')
@click.pass_context
def init(ctx, apikey, url, skill_name):
    """
    Enable the creation of a skill sandbox for other git branches

    Downloads from WA the skill <skill_name> and decomposes it to files in
    <project_folder>/waw/<skill_name>. This should be executed on your main
    git branch, and the decomposed files committed to it.
    """
    Sandbox(apikey, url, skill_name).init()


@sandbox.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True, metavar='<skill_name>')
@click.pass_context
@protect_readonly
def push(ctx, apikey, url, skill_name):
    """
    Reassemble a skill and deploy it as a sandbox

    Deploys the files in <project_folder>/waw/<skill_name> as a WA skill named
    "<gitbranch>__<skill_name>
    """
    Sandbox(apikey, url, skill_name).push()


@sandbox.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True, metavar='<skill_name>')
@click.pass_context
def pull(ctx, apikey, url, skill_name):
    """
    Overwrite the decomposed skill with the contents of a sandbox

    Download the WA skill "<git_branch>__<skill_name>" and decompose it
    to files in <project_folder>/waw/<skill_name>
    """
    Sandbox(apikey, url, skill_name).pull()


@sandbox.command(name='delete')
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True, metavar='<skill_name>')
@click.pass_context
@protect_readonly
def delete_sandbox(ctx, apikey, url, skill_name):
    """
    Deletes the Watson Assistant skill <git_branch>__<skill_name>

    No files are deleted by this command.
    """
    Sandbox(apikey, url, skill_name).delete()


class Sandbox(object):

    PREFIX_SEPARATOR = '__'

    def __init__(self, apikey, url, skill_name):
        self.apikey = apikey
        self.url = url
        self.branch = git.current_branch()
        if self.branch == cfg.main_branch():
            prefix = ''
        else:
            prefix = self.branch + self.PREFIX_SEPARATOR
            if skill_name.startswith(prefix):
                skill_name = skill_name[len(prefix):]
        self.skill_name = skill_name
        self.sandbox_name = prefix + self.skill_name
        # print(f'{self.branch=} {self.skill_name=} {prefix=} {self.sandbox_name=}')

    @staticmethod
    def _error(msg):
        click.secho(msg, fg='white', bg='red')
        sys.exit(1)

    def _check_current_branch(self, must_be_master):
        if not self.branch:
            self._error("Your wa-cli project needs to be under git version control to create a sandbox.")
        is_master = self.branch == cfg.main_branch()
        if not must_be_master and is_master:
            self._error("A sandbox cannot be push/pulled while on the main git branch.\n"
                        "Create the branch for your sandbox with git checkout -b branch_name")
        elif must_be_master and not is_master:
            self._error(f"A sandbox needs to be initialized from the main git branch ({cfg.main_branch()}).\n"
                        f"Create the branch for your sandbox with git checkout -b branch_name")

    def _check_skill_decomposed(self):
        skill_folder = os.path.join(cfg.waw_target_folder(), self.skill_name)
        if not os.path.isdir(skill_folder):
            self._error(f"No folder named {self.skill_name} in <project_root>/waw")
        if not git.skill_is_in_master(self.skill_name):
            self._error(f"The skill does not exist in the main branch '{cfg.main_branch()}'")

    def push(self):
        self._check_current_branch(must_be_master=False)
        self._check_skill_decomposed()
        skill_file = workbench.reassemble_skill_file(skill_name=self.skill_name,
                                                     new_name=self.sandbox_name,
                                                     force=True)
        wa.deploy_skill(self.apikey, self.url, skill_file, force=True)
        click.echo('Done!')

    def _decompose(self, skill_name: str):
        skill_file = wa.get_skill(self.apikey, self.url, self.sandbox_name)
        if not skill_file:
            sys.exit(1)
        else:
            workbench.decompose_skill_file(skill_file, self.skill_name)

    def _revert_metadata_changes(self):
        meta_file = os.path.join(cfg.waw_target_folder(), self.skill_name, 'meta.json')

        with open(meta_file, 'r') as json_file:
            meta = json.load(json_file)
        meta['name'] = self.skill_name

        description_prefix = f'Copied from {self.skill_name}. '
        if meta['description'].startswith(description_prefix):
            meta['description'] = meta['description'][len(description_prefix):]

        with open(meta_file, 'w', encoding='utf-8') as json_file:
            json.dump(meta, json_file, ensure_ascii=False, indent=4)

    def pull(self):
        self._check_current_branch(must_be_master=False)
        self._decompose(self.sandbox_name)
        self._revert_metadata_changes()
        click.echo('Done!')

    def init(self):
        self._check_current_branch(must_be_master=True)
        self._decompose(self.skill_name)

    def delete(self):
        self._check_current_branch(must_be_master=False)
        wa.delete_skill(self.apikey, self.url, name=self.sandbox_name)
