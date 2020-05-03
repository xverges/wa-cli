
import os
import subprocess

from .cfg import WAW_FOLDER, main_branch


def _run_command(command: list) -> str:
    return subprocess.run(command, stdout=subprocess.PIPE).stdout.decode('utf-8')


def current_branch() -> str:
    if 'TRAVIS_PULL_REQUEST_BRANCH' in os.environ:
        if os.environ['TRAVIS_PULL_REQUEST_BRANCH']:
            return 'PR_' + os.environ['TRAVIS_PULL_REQUEST_BRANCH']
    if 'TRAVIS_BRANCH' in os.environ:
        return os.environ['TRAVIS_BRANCH']
    output = _run_command(['git', 'branch'])

    for line in output.splitlines():
        if line.startswith('*'):
            return line.split()[1]
    return ''


def skill_is_in_master(skill_name: str) -> bool:
    if 'TRAVIS' in os.environ and os.environ['TRAVIS'] == 'true':
        return True
    output = _run_command(['git', 'ls-tree', f'{main_branch()}:{WAW_FOLDER}/{skill_name}'])
    return output and len(output.split()) >= 6
