
import errno
import inspect
import os
import sys

import click


WACLI_FOLDER = '.wa-cli'
WACLI_CFG = 'wa-cli.cfg'
SKILLS_FOLDER = 'skills'
TEST_FOLDER = 'test'
WAW_FOLDER = 'waw'
READONLY_SERVICES = 'readonly_services.txt'
MAIN_BRANCH = 'main_branch.txt'


def init(apikey: str,
         url: str,
         apikey_src: str,
         url_src: str,
         main_branch: str) -> None:

    def current_contents(file_name):
        if os.path.isfile(file_name):
            with open(file_name, 'r') as _file:
                return [line.strip() for line in _file.readlines()]
        return []

    def update_contents(file_name, contents):
        with open(file_name, 'w') as _file:
            _file.write("\n".join(contents))

    cfg_file = '.env'
    contents = current_contents(cfg_file)
    contents = update_env_contents(contents, apikey, url, apikey_src, url_src)
    update_contents(cfg_file, contents)

    cfg_file = '.gitignore'
    contents = current_contents(cfg_file)
    contents = update_gitignore_contents(contents)
    update_contents(cfg_file, contents)

    for folder in [WACLI_FOLDER, SKILLS_FOLDER, TEST_FOLDER, WAW_FOLDER]:
        if not os.path.isdir(folder):
            os.mkdir(folder)

    cfg_file = os.path.join(WACLI_FOLDER, READONLY_SERVICES)
    contents = current_contents(cfg_file)
    if apikey_src:
        if not any([x == apikey_src for x in contents]):
            contents.append(apikey_src)
    update_contents(cfg_file, contents)

    cfg_file = _main_branch_file()
    with open(cfg_file, 'w') as _file:
        _file.write(main_branch)


_cache = {'project_folder': '',
          'code_folder': '',
          'cfg': {}}


def get_project_folder() -> str:
    if not _cache['project_folder']:
        current_folder = os.getcwd()
        while True:
            if os.path.isdir(os.path.join(current_folder, WACLI_FOLDER)):
                _cache['project_folder'] = current_folder
                break
            parent_folder = os.path.dirname(current_folder)
            if parent_folder != current_folder:
                current_folder = parent_folder
                continue
            break
    return _cache['project_folder']


def get_code_folder() -> str:
    if not _cache['code_folder']:
        for folder in sys.path:
            if os.path.isfile(os.path.join(folder, WACLI_CFG)):
                _cache['code_folder'] = folder
                break
    return _cache['code_folder']


def get_cfg_value(key: str) -> str:
    if not _cache['cfg']:
        cfg_path = os.path.join(get_code_folder(), WACLI_CFG)
        with open(cfg_path, 'r') as cfg_file:
            for line in cfg_file:
                line = line.strip()
                if line and '=' in line:
                    k, v = tuple([fragment.strip() for fragment in line.split('=')])
                    _cache['cfg'][k] = v
    return _cache['cfg'][key]


def skills_folder() -> str:

    return os.path.join(get_project_folder(), SKILLS_FOLDER)


def test_folder() -> str:

    return os.path.join(get_project_folder(), TEST_FOLDER)


def test_scripts_folder() -> str:

    return get_cfg_value('WA_TEST_TOOL_PATH')


def waw_target_folder() -> str:

    return os.path.join(get_project_folder(), WAW_FOLDER)


def waw_scripts_folder() -> str:

    return os.path.join(get_cfg_value('WAW_PATH'), "scripts")


def _main_branch_file() -> str:
    folder = get_project_folder()
    return os.path.join(folder, WACLI_FOLDER, MAIN_BRANCH)


def main_branch() -> str:
    with open(_main_branch_file(), 'r') as _file:
        for line in _file.readlines():
            if line and not line.startswith('#'):
                return line.strip()


def check_context(ctx):
    folder = get_project_folder()
    if not folder:
        msg = "This is not a wa-cli project. You'll need to run wa-cli init."
        click.secho(msg, fg='white', bg='red')
        folder = os.path.join(os.getcwd(), WACLI_FOLDER)
        sys.exit(FileNotFoundError(errno.ENOENT, msg, folder))

    ctx.ensure_object(dict)
    ctx.obj['project_folder'] = folder
    os.chdir(folder)

    branch_file = _main_branch_file()
    if not os.path.isfile(branch_file):
        msg = f"The {WACLI_FOLDER} folder is missing the {MAIN_BRANCH} file. You'll need to run wa-cli init."
        click.secho(msg, fg='white', bg='red')
        sys.exit(FileNotFoundError(errno.ENOENT, msg, branch_file))
    if not main_branch():
        msg = f"Wrong contents in {branch_file}. You'll need to run wa-cli init."
        click.secho(msg, fg='white', bg='red')
        sys.exit(1)


def update_env_contents(existing_lines: list,
                        apikey: str,
                        url: str,
                        apikey_src: str,
                        url_src) -> list:
    header = '# set -o allexport; source .env; set +o allexport'
    vars = {
        'WA_APIKEY': apikey,
        'WA_URL': url,
        'WA_APIKEY_SRC': apikey_src,
        'WA_URL_SRC': url_src
    }
    new_lines = []

    def append(var_name, value):
        value = value if value else ''
        line = f'{var_name}={value}'
        new_lines.append(line)

    if not any([x == header for x in existing_lines]):
        new_lines.append(header)
    for existing in existing_lines:
        replaced = False
        for var_name, value in vars.items():
            if existing.startswith(f'{var_name}='):
                if existing != f'{var_name}=':
                    new_lines.append(f'# {existing}')
            else:
                continue
            append(var_name, value)
            del vars[var_name]
            replaced = True
            break

        if not replaced:
            new_lines.append(existing)
    for var_name, value in vars.items():
        append(var_name, value)
    return new_lines


def update_gitignore_contents(existing_lines: list) -> list:
    entries = """
    /.env
    /.wa-cli/readonly_services.txt
    /waw/re-assembled
    /test/*/data/kfold/*
    /test/*/data/workspace_base.json
    /test/*/data/*-train.csv
    wa_json
    log.log
    .DS_Store
    """
    entries = [entry for entry in inspect.cleandoc(entries).splitlines() if entry.strip()]
    entries.append('')  # append a blank line
    for entry in entries:
        if not any([(line.strip() == entry) for line in existing_lines]):
            existing_lines.append(entry)
    return existing_lines
