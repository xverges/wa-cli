import os

import click

apikey = click.option('--apikey',
                      default=lambda: os.environ.get('WA_APIKEY', ''),
                      show_default="Value of WA_APIKEY", required=True)
url = click.option('--url',
                   default=lambda: os.environ.get('WA_URL', ''),
                   show_default="Value of WA_URL", required=True)

mandatory = [apikey, url]


def add(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options
