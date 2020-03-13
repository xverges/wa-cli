#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os

import click
from .helpers import protect_readonly
from .helpers import common_options
from .helpers import cfg
from .wa import wa


@click.group()
@click.pass_context
def service(ctx):
    """
    Service related commands
    """
    cfg.check_context(ctx)


@service.command()
@common_options.add(common_options.mandatory)
@click.pass_context
@protect_readonly
def delete_all(ctx, apikey, url):
    """
    Delete all the skill in the service
    """
    success = wa.delete_all_skills(apikey, url)
    click.echo(f'Success: {success}')


@service.command()
@common_options.add(common_options.mandatory)
@click.option('--src_apikey',
              default=lambda: os.environ.get('WA_APIKEY_SRC', ''),
              callback=common_options.non_empty,
              show_default="Value of WA_APIKEY_SRC", required=True)
@click.option('--src_url',
              default=lambda: os.environ.get('WA_URL_SRC', ''),
              callback=common_options.non_empty,
              show_default="Value of WA_URL_SRC", required=True)
@click.option('--force', is_flag=True)
@click.pass_context
@protect_readonly
def clone_skills(ctx, apikey, url, src_apikey, src_url, force):
    """
    Clone the skills from a service into another
    """
    wa.clone_service_skills(apikey, url, src_apikey, src_url, force)


@service.command()
@common_options.add(common_options.mandatory)
@click.option('--force', is_flag=True)
@click.pass_context
def download_skills(ctx, apikey, url, force):
    """
    Download all the skills from a service
    """
    wa.download_service_skills(apikey, url, force)
