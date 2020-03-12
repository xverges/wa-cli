import os

import click


def non_empty(ctx, param, value):
    if not value:
        raise click.BadParameter(f"cannot be empty.")
    return value


apikey = click.option('--apikey',
                      default=lambda: os.environ.get('WA_APIKEY', ''),
                      callback=non_empty,
                      show_default="Value of WA_APIKEY", required=True)
url = click.option('--url',
                   default=lambda: os.environ.get('WA_URL', ''),
                   callback=non_empty,
                   show_default="Value of WA_URL", required=True)

mandatory = [apikey, url]


def add(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options
