
import subprocess

from .cfg import WAW_FOLDER, main_branch


def _run_command(command: list) -> str:
    return subprocess.run(command, stdout=subprocess.PIPE).stdout.decode('utf-8')


def current_branch() -> str:
    output = _run_command(['git', 'branch'])
    for line in output.splitlines():
        if line.startswith('*'):
            return line.split()[1]
    return ''


def skill_is_in_master(skill_name: str) -> bool:
    output = _run_command(['git', 'ls-tree', f'{main_branch()}:{WAW_FOLDER}/{skill_name}'])
    return output and len(output.split()) >= 6
