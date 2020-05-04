#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import os
import sys
import time

import click
from .helpers import protect_readonly
from .helpers import common_options
from .helpers import cfg
from .helpers import git
from .wa import wa
from .wa_testing import wa_testing
from .workbench import workbench


@click.group()
@click.pass_context
def sandbox(ctx):
    """
    Work with skills in a branch-dependant sandbox.

    \b
    Sample workflow:
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
def deploy(ctx, apikey, url, skill_name):
    """
    Reassemble a skill and deploy it

    Deploys the files in <project_folder>/waw/<skill_name>. Must be executed from the
    main git branch.
    """
    Sandbox(apikey, url, skill_name).deploy()


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


@sandbox.command()
@click.argument('skill_name', type=click.STRING, required=True, metavar='<skill_name>')
@click.pass_context
def name(ctx, skill_name):
    """
    Display the <skill_name> sandbox name associated with the current branch/travis build
    """
    sandbox = Sandbox('', '', skill_name)
    click.echo(sandbox.sandbox_name)


@sandbox.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
@click.option('--timeout', default=300, show_default=True, help='Timeout in seconds')
@click.pass_context
def wait_for_ready(ctx, apikey, url, skill_name, timeout):
    """
    Wait for a skill sandbox to be trained after deployment

    Returns 1 if timeout expires before the skill is ready, 0 otherwise.
    """
    sys.exit(Sandbox(apikey, url, skill_name).wait_for_ready(timeout))


@click.group()
def test():
    """
    Test related commands
    """


@test.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
@click.option('--folds', default=5, show_default=True)
@click.option('--show-graphics', is_flag=True, help='Open a browser with the generated images')
def kfold(apikey, url, skill_name, folds, show_graphics):
    """
    k-fold test to measure ground truth consistency

    \b
    The test data is obtained from the skill deployed as a sandbox.
    See https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/kfold.md for details
    """
    sandbox = Sandbox(apikey, url, skill_name)
    output_dir = wa_testing.output_dir_for_skill(skill_name, 'kfold')
    wa_testing.k_fold(apikey, url, '', folds, show_graphics, skill_name=sandbox.sandbox_name, output_dir=output_dir)


@test.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
@click.option('--show-graphics', is_flag=True, help='Open a browser with the generated images')
def blind(apikey, url, skill_name, show_graphics):
    """
    blind test using a CSV file with utterances and expected intents

    \b
    The tests will be run on the skill deployed as a sandbox.
    The file <project_root>/test/blind/<skill_name>/input.csv will be used as input.
    See https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/blind.md for details
    """
    sandbox = Sandbox(apikey, url, skill_name)
    output_dir = wa_testing.output_dir_for_skill(skill_name, 'blind')
    wa_testing.blind(apikey, url, sandbox.sandbox_name, show_graphics, output_dir=output_dir)


@test.command()
@common_options.add(common_options.mandatory)
@click.argument('skill_name', type=click.STRING, required=True)
def flow(apikey, url, skill_name):
    """
    dialog flow test

    \b
    The tests will be run on the skill deployed as a sandbox.
    Files matching <project_root>/test/flow/<skill_name>/*.tsv will be used as input. Example input:
    https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/dialog_test/tests/Customer_Care_Test.tsv
    You can start an new conversation specifying NEWCONVERSATION as the user input.
    """
    sandbox = Sandbox(apikey, url, skill_name)
    output_dir = wa_testing.output_dir_for_skill(skill_name, 'flow')
    rc = wa_testing.flow(apikey, url, sandbox.sandbox_name, output_dir=output_dir)
    if rc:
        sys.exit(rc)


sandbox.add_command(test)


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

    def deploy(self):
        self._check_current_branch(must_be_master=True)
        self._check_skill_decomposed()
        skill_file = workbench.reassemble_skill_file(skill_name=self.skill_name,
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

    def wait_for_ready(self, timeout):
        start_time = time.time()
        id = wa.workspace_id_from_skill_name(self.apikey, self.url, self.sandbox_name)
        if not id:
            click.echo(f'"{self.sandbox_name}" was not found status. Not waiting.')
            return 1

        while time.time() - start_time < timeout:
            status = wa.get_skill_status(self.apikey, self.url, id)
            if status == 'Available':
                return 0
            elif status == 'Training':
                time.sleep(15)
            else:
                click.echo(f'"{self.sandbox_name}" status is {status}. Not waiting.')
                return 1
        click.echo(f'"{self.sandbox_name}" readiness timed out')
        return 1
