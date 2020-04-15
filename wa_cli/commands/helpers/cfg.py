
import errno
import inspect
import os
import subprocess
import sys

import click


WACLI_FOLDER = '.wa-cli'
WACLI_CFG = 'wa-cli.cfg'
SKILLS_FOLDER = 'skills'
TEST_FOLDER = 'test'
WAW_FOLDER = 'waw'
READONLY_SERVICES = 'readonly_services.txt'
MAIN_BRANCH = 'main_branch.txt'

GIT_WAW = ('https://github.com/xverges/watson-assistant-workbench.git', '95afc59')
GIT_WTT = ('https://github.com/cognitive-catalyst/WA-Testing-Tool.git', 'fe28739')

_cache = {'project_folder': '',
          'code_folder': '',
          'cfg': {}}


def init():

    click.confirm('This will initialise the current folder as a wa-cli project. Continue?',
                  abort=True,
                  default=True)
    _check_dependencies()

    apikey, url, apikey_src, url_src, main_branch = _init_prompt()

    cfg_file = '.env'
    contents = read_file_contents(cfg_file)
    env_setup = get_env_setup_line()
    header = f'# {env_setup}'
    vars = {
        'WA_APIKEY': apikey,
        'WA_URL': url,
        'WA_APIKEY_SRC': apikey_src,
        'WA_URL_SRC': url_src
    }
    contents = update_env_contents(contents, vars, header)
    write_file_contents(cfg_file, contents)

    cfg_file = '.gitignore'
    contents = read_file_contents(cfg_file)
    contents = update_gitignore_contents(contents)
    write_file_contents(cfg_file, contents)

    for folder in [WACLI_FOLDER, SKILLS_FOLDER, TEST_FOLDER, WAW_FOLDER]:
        if not os.path.isdir(folder):
            os.mkdir(folder)

    cfg_file = os.path.join(WACLI_FOLDER, READONLY_SERVICES)
    contents = read_file_contents(cfg_file)
    if apikey_src:
        if not any([x == apikey_src for x in contents]):
            contents.append(apikey_src)
    write_file_contents(cfg_file, contents)

    cfg_file = _main_branch_file()
    with open(cfg_file, 'w') as _file:
        _file.write(main_branch)

    click.echo('The values you have supplied have been added to the .env file')
    click.echo('You can set them as environment variables\n'
               'and enable command completion by running \n\n'
               '   ' + env_setup + '\n\n'
               'You don''t need to remember this: run "wa-cli env" to be reminded')


def env_help():
    click.echo('Set the environment variables that "wa-cli init" added to the .env file\n'
               'and enable command completion by running \n\n'
               '   ' + get_env_setup_line() + '\n')


def _init_prompt():
    apikey = click.prompt('Enter the apikey of the service that you are going to be targeting', '')
    url = click.prompt('Enter the url of the service that you are going to be targeting', '')
    apikey_src = click.prompt('If you plan to clone skills from a different service, enter its apikey', '')
    url_src = click.prompt('If you plan to clone skills from a different service, enter its url', '')
    main_branch = click.prompt('Enter your main branch. Usually, "master"', 'master')
    return (apikey, url, apikey_src, url_src, main_branch)


def read_file_contents(file_name):
    if os.path.isfile(file_name):
        with open(file_name, 'r') as _file:
            return [line.strip() for line in _file.readlines()]
    return []


def write_file_contents(file_name, contents):
    with open(file_name, 'w') as _file:
        _file.write("\n".join(contents))


def shell_completion():
    shell = os.getenv('SHELL', '/bin/bash')
    source = 'source_bash'
    if 'fish' in shell:
        source = 'source_fish'
    elif 'zsh' in shell:
        source = 'source_zsh'
    return 'eval "$(_WA_CLI_COMPLETE=' + source + ' wa-cli)"'


def get_env_setup_line():
    return f'set -o allexport; source .env; set +o allexport; {shell_completion()}'


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
            folder = os.path.join(folder, 'wa_cli')
            if os.path.isfile(os.path.join(folder, '__init__.py')):
                folder = os.path.abspath(folder)
                _cache['code_folder'] = folder
                break
    return _cache['code_folder']


def get_common_cfg_file() -> str:
    return os.path.join(get_code_folder(), WACLI_CFG)


def get_cfg_value(key: str) -> str:
    if not _cache['cfg']:
        cfg_file_path = get_common_cfg_file()
        if os.path.isfile(cfg_file_path):
            with open(cfg_file_path, 'r') as cfg_file:
                for line in cfg_file:
                    line = line.strip()
                    if not line.startswith('#') and '=' in line:
                        k, v = tuple([fragment.strip() for fragment in line.split('=')])
                        _cache['cfg'][k] = v
    return _cache['cfg'].get(key, '')


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
                        vars: dict,
                        header: str) -> list:
    new_lines = []

    def append(var_name, value):
        value = value if value else ''
        line = f'{var_name}={value}'
        new_lines.append(line)

    if header and not any([x == header for x in existing_lines]):
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


def _check_dependencies():

    def download_repo(repo_url, sha, folder_name, base_folder):
        full_path = os.path.join(base_folder, folder_name)
        if not os.path.isdir(full_path):
            click.echo(f'Cloning {repo_url}... to {full_path}')
            command = ['git', 'clone',  repo_url, folder_name]
            subprocess.check_call(command,
                                  cwd=base_folder,
                                  stderr=subprocess.DEVNULL,
                                  stdout=subprocess.DEVNULL)
        command = ['git', 'fetch']
        subprocess.check_call(command,
                              cwd=full_path,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL)
        command = ['git', 'checkout', sha]
        subprocess.check_call(command,
                              cwd=full_path,
                              stderr=subprocess.DEVNULL,
                              stdout=subprocess.DEVNULL)
        return full_path

    waw_path = get_cfg_value('WAW_PATH')
    waw_test_tool_path = get_cfg_value('WA_TEST_TOOL_PATH')
    update_cfg = not waw_path or \
                 not waw_test_tool_path or \
                 not os.path.isdir(waw_path) or \
                 not os.path.isdir(waw_test_tool_path)

    base_folder = os.path.join(get_code_folder(), 'tools')
    os.makedirs(base_folder, exist_ok=True)
    waw_path = download_repo(GIT_WAW[0], GIT_WAW[1], 'watson-assistant-workbench', base_folder)
    waw_test_tool_path = download_repo(GIT_WTT[0], GIT_WTT[1], 'WA-Testing-Tool', base_folder)

    if update_cfg:
        vars = {
            'WAW_PATH': waw_path,
            'WA_TEST_TOOL_PATH': waw_test_tool_path
        }
        cfg_file = get_common_cfg_file()
        cfg_contents = read_file_contents(cfg_file)
        cfg_contents = update_env_contents(cfg_contents, vars, '')
        write_file_contents(cfg_file, cfg_contents)
        click.echo('\n')
