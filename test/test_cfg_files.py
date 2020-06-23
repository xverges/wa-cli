
import inspect

from wa_cli.commands.helpers import cfg


existing_env = """
               WA_APIKEY=old_1
               WA_URL=

               # random comment
               RANDOM_VAR=33
               WA_APIKEY_SRC=old_3
               WA_URL_SRC=old_4"""


def env_vars(apikey: str,
             url: str,
             apikey_src: str,
             url_src: str):
    return {
        'WA_APIKEY': apikey,
        'WA_URL': url,
        'WA_APIKEY_SRC': apikey_src,
        'WA_URL_SRC': url_src
    }


def test_empty_file_all_params():
    header = '# set -o allexport; source .env; set +o allexport'
    expected = [
        '# set -o allexport; source .env; set +o allexport',
        'WA_APIKEY=1',
        'WA_URL=2',
        'WA_APIKEY_SRC=3',
        'WA_URL_SRC=4'
    ]
    assert cfg.update_env_contents([], env_vars('1', '2', '3', '4'), header) == expected


def test_empty_file_one_missing_param():
    header = '# set -o allexport; source .env; set +o allexport'
    expected = [
        '# set -o allexport; source .env; set +o allexport',
        'WA_APIKEY=1',
        'WA_URL=2',
        'WA_APIKEY_SRC=',
        'WA_URL_SRC=4'
    ]
    assert cfg.update_env_contents([], env_vars('1', '2', '', '4'), header) == expected


def test_existing_cfg_file():
    header = '# set -o allexport; source .env; set +o allexport'
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
    assert cfg.update_env_contents(input_lines, env_vars('1', '2', '', '4'), header) == expected


def test_existing_gitignore_without_1():
    existing = [
        '# random comment',
        '# /.env',
        '#    /skills',
    ]
    expected = [
        '# random comment',
        '# /.env',
        '#    /skills',
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    updated = cfg.update_gitignore_contents(existing)
    assert updated[:len(expected)] == expected
    assert '/skills' not in updated


def test_existing_gitignore_without_2():
    existing = [
        '# random comment',
        '# /.env',
        '#skills',
    ]
    expected = [
        '# random comment',
        '# /.env',
        '#skills',
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    updated = cfg.update_gitignore_contents(existing)
    assert updated[:len(expected)] == expected
    assert '/skills' not in updated


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
    updated = cfg.update_gitignore_contents(existing)
    assert updated[:len(expected)] == expected
    assert '/skills' in updated


def test_no_gitignore():
    existing = []
    expected = [
        '/.env',
        '/.wa-cli/readonly_services.txt'
    ]
    updated = cfg.update_gitignore_contents(existing)
    assert updated[:len(expected)] == expected
    assert '/skills' in updated
