
import inspect

from wa_cli.commands.helpers import cfg


existing_env = """
               WA_APIKEY=old_1
               WA_URL=

               # random comment
               RANDOM_VAR=33
               WA_APIKEY_SRC=old_3
               WA_URL_SRC=old_4"""


def test_empty_file_all_params():
    expected = [
        '# set -o allexport; source .env; set +o allexport',
        'WA_APIKEY=1',
        'WA_URL=2',
        'WA_APIKEY_SRC=3',
        'WA_URL_SRC=4'
    ]
    assert cfg.update_env_contents([], '1', '2', '3', '4') == expected


def test_empty_file_one_missing_param():
    expected = [
        '# set -o allexport; source .env; set +o allexport',
        'WA_APIKEY=1',
        'WA_URL=2',
        'WA_APIKEY_SRC=',
        'WA_URL_SRC=4'
    ]
    assert cfg.update_env_contents([], '1', '2', '', '4') == expected


def test_existing_cfg_file():
    expected = [
        '# set -o allexport; source .env; set +o allexport',
        '# WA_APIKEY=old_1',
        'WA_APIKEY=1',
        'WA_URL=2',
        '',
        '# random comment',
        'RANDOM_VAR=33',
        '# WA_APIKEY_SRC=old_3',
        'WA_APIKEY_SRC=',
        '# WA_URL_SRC=old_4',
        'WA_URL_SRC=4'
    ]
    input_lines = inspect.cleandoc(existing_env).split('\n')
    assert cfg.update_env_contents(input_lines, '1', '2', '', '4') == expected


def test_existing_gitignore_without():
    existing = [
        '# random comment',
        '# /.env'
    ]
    expected = [
        '# random comment',
        '# /.env',
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    assert cfg.update_gitignore_contents(existing)[:4] == expected[:4]


def test_existing_gitignore_with():
    existing = [
        '# random comment',
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    expected = [
        '# random comment',
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    assert cfg.update_gitignore_contents(existing)[:3] == expected[:3]


def test_no_gitignore():
    existing = []
    expected = [
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    assert cfg.update_gitignore_contents(existing)[:2] == expected[:2]
