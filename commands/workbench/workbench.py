
import json
import os
import subprocess
import sys
from typing import List

from ..helpers import cfg


class workbench(object):

    @classmethod
    def _make_decompose_folders(cls, skill_name: str):
        names = ['wa_json', 'counterexamples', 'intents', 'entities', 'dialog']
        root = cfg.waw_target_folder()
        for name in names:
            os.makedirs(os.path.join(root, skill_name, name), exist_ok=True)

    @classmethod
    def _to_smaller_json_files(cls, full_path: str, skill_name: str):
        root = cfg.waw_target_folder()
        command_line = [
            sys.executable,
            os.path.join(cfg.waw_scripts_folder(), 'workspace_decompose.py'),
            full_path,
            '-i', os.path.join(root, skill_name, 'wa_json', 'intents.json'),
            '-c', os.path.join(root, skill_name, 'wa_json', 'counterexamples.json'),
            '-e', os.path.join(root, skill_name, 'wa_json', 'entities.json'),
            '-d', os.path.join(root, skill_name, 'wa_json', 'dialog.json'),
        ]
        # print(f'{" ".join(command_line)}')
        completed = subprocess.run(command_line,
                                   stderr=sys.stderr, stdout=sys.stdout)
        if completed.returncode != 0:
            raise RuntimeError('Failure in waw workspace_decompose.py')

    @classmethod
    def _run_transformation_script(cls,
                                   skill_name: str,
                                   script_name: str,
                                   types_of_files: List[str]):

        root = cfg.waw_target_folder()
        for type_of_file in types_of_files:
            command_line = [
                sys.executable,
                os.path.join(cfg.waw_scripts_folder(), script_name),
                os.path.join(root, skill_name, 'wa_json', f'{type_of_file}.json'),
                os.path.join(root, skill_name, f'{type_of_file}')
            ]
            # print(f'{" ".join(command_line)}')
            completed = subprocess.run(command_line,
                                       stderr=sys.stderr, stdout=sys.stdout)
            if completed.returncode != 0:
                raise RuntimeError(f'Failure in waw {script_name}')

    @classmethod
    def _to_csv_intents(cls, skill_name: str):
        cls._run_transformation_script(skill_name, 'intents_json2csv.py', ['intents', 'counterexamples'])

    @classmethod
    def _to_csv_entities(cls, skill_name: str):
        cls._run_transformation_script(skill_name, 'entities_json2csv.py', ['entities'])

    @classmethod
    def _to_xml_dialog(cls, skill_name: str):
        # Cannot use _run_transformation_script because it has an additional flag
        root = cfg.waw_target_folder()
        script_name = 'dialog_json2xml.py'
        for type_of_file in ['dialog']:
            command_line = [
                sys.executable,
                os.path.join(cfg.waw_scripts_folder(), script_name),
                os.path.join(root, skill_name, 'wa_json', f'{type_of_file}.json'),
                '-d', os.path.join(root, skill_name, f'{type_of_file}')
            ]
            # print(f'{" ".join(command_line)}')
            completed = subprocess.run(command_line,
                                       stderr=sys.stderr, stdout=sys.stdout)
            if completed.returncode != 0:
                raise RuntimeError(f'Failure in waw {script_name}')

    @classmethod
    def _get_skill_name(cls, full_path: str) -> str:
        with open(full_path, 'r') as json_file:
            cached = json.load(json_file)
            return cached['name']

    @classmethod
    def decompose_skill_file(cls, full_path: str) -> bool:
        full_path = os.path.abspath(full_path)
        skill_name = cls._get_skill_name(full_path)
        cls._make_decompose_folders(skill_name)
        cls._to_smaller_json_files(full_path, skill_name)
        cls._to_csv_intents(skill_name)
        cls._to_csv_entities(skill_name)
        cls._to_xml_dialog(skill_name)

    @classmethod
    def decompose_all(cls, apikey: str, url: str) -> bool:
        pass
