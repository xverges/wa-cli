
from collections import OrderedDict
from glob import glob
import json
import os
import shutil
import subprocess
import sys
from typing import List

import click

from ..helpers import cfg


class workbench(object):

    _root = cfg.waw_target_folder()

    @classmethod
    def _make_decompose_folders(cls, skill_name: str):
        skill_folder = os.path.join(cls._root, skill_name)
        if os.path.isdir(skill_folder):
            shutil.rmtree(skill_folder, ignore_errors=True)
        names = ['wa_json', 'counterexamples', 'intents', 'entities', 'dialog']
        for name in names:
            os.makedirs(os.path.join(skill_folder, name), exist_ok=True)

    @classmethod
    def _make_reassemble_folder(cls, skill_name: str) -> str:
        folder = os.path.join(cls._root, 're-assembled', skill_name)
        os.makedirs(folder, exist_ok=True)
        return folder

    @classmethod
    def _run_waw_script(cls, script_name: str, params: List[str]):
        command_line = [
            sys.executable,
            os.path.join(cfg.waw_scripts_folder(), script_name)]
        command_line.extend(params)
        # command_line.append('--verbose')
        print(f'===> {" ".join(command_line)}')
        completed = subprocess.run(command_line,
                                   stderr=sys.stderr, stdout=sys.stdout)
        if completed.returncode != 0:
            raise RuntimeError(f'Failure in waw {script_name}')

    @classmethod
    def _to_smaller_json_files(cls, full_path: str, skill_name: str, meta: dict):
        cls._run_waw_script('workspace_decompose.py', [
            full_path,
            '-i', os.path.join(cls._root, skill_name, 'wa_json', 'intents.json'),
            '-c', os.path.join(cls._root, skill_name, 'wa_json', 'counterexamples.json'),
            '-e', os.path.join(cls._root, skill_name, 'wa_json', 'entities.json'),
            '-d', os.path.join(cls._root, skill_name, 'wa_json', 'dialog.json'),
        ])
        meta_full_path = os.path.join(cls._root, skill_name, 'meta.json')
        with open(meta_full_path, 'w', encoding='utf-8') as json_file:
            json.dump(meta, json_file, ensure_ascii=False, indent=4)

    @classmethod
    def _run_to_csv_script(cls,
                           skill_name: str,
                           script_name: str,
                           types_of_files: List[str]):

        for type_of_file in types_of_files:
            cls._run_waw_script(script_name, [
                os.path.join(cls._root, skill_name, 'wa_json', f'{type_of_file}.json'),
                os.path.join(cls._root, skill_name, f'{type_of_file}')
            ])

    @classmethod
    def _to_csv_intents(cls, skill_name: str):
        cls._run_to_csv_script(skill_name, 'intents_json2csv.py', ['intents', 'counterexamples'])

    @classmethod
    def _to_csv_entities(cls, skill_name: str):
        cls._run_to_csv_script(skill_name, 'entities_json2csv.py', ['entities'])

    @classmethod
    def _to_xml_dialog(cls, skill_name: str):
        # Cannot use _run_to_csv_script because it has an additional flag
        cls._run_waw_script('dialog_json2xml.py', [
            os.path.join(cls._root, skill_name, 'wa_json', 'dialog.json'),
            '--dialogDir', os.path.join(cls._root, skill_name, 'dialog')
        ])

    @classmethod
    def _reassemble_dialog(cls, skill_name: str, tgt_folder: str):
        script_folder = cfg.waw_scripts_folder()
        schema_file = os.path.join(os.path.dirname(script_folder), 'data_spec', 'dialog_schema.xml')
        cls._run_waw_script('dialog_xml2json.py', [
            '--common_dialog_main', os.path.join(cls._root, skill_name, 'dialog', 'dialog.xml'),
            '--common_outputs_directory', tgt_folder,
            '--common_outputs_dialogs', 'dialog.json',
            '--common_schema', schema_file
        ])

    @classmethod
    def _reassemble_entities(cls, skill_name: str, tgt_folder: str):
        cls._run_waw_script('entities_csv2json.py', [
            '--common_entities', os.path.join(cls._root, skill_name, 'entities'),
            '--common_outputs_directory', tgt_folder,
            '--common_outputs_entities', 'entities.json',
            '--common_soft'
        ])

    @classmethod
    def _reassemble_intents(cls, skill_name: str, tgt_folder: str):
        for file_type in ['intents', 'counterexamples']:
            cls._run_waw_script('intents_csv2json.py', [
                '--common_intents', os.path.join(cls._root, skill_name, file_type),
                '--common_outputs_directory', tgt_folder,
                '--common_outputs_intents', f'{file_type}.json'
            ])

    @classmethod
    def _reassemble_reassembled_json_files(cls, skill_name: str, tgt_folder: str):

        meta_file = os.path.join(cls._root, skill_name, 'meta.json')
        with open(meta_file, 'r', encoding='utf-8') as json_file:
            meta = json.load(json_file)
            new_name = os.path.basename(tgt_folder)
            if skill_name != new_name:
                meta['description'] = f'Copied from {skill_name}. {meta["description"]}'
                skill_name = new_name
        cls._run_waw_script('workspace_compose.py', [
            '--common_outputs_directory', tgt_folder,
            '--common_outputs_workspace', 'skill.json',
            '--common_outputs_intents', 'intents.json',
            '--common_outputs_counterexamples', 'counterexamples.json',
            '--common_outputs_entities', 'entities.json',
            '--common_outputs_dialogs', 'dialog.json',
            '--conversation_workspace_name', skill_name,
            '--conversation_language', meta['language'],
            '--conversation_description', meta['description']
        ])
        preferred_sorting = ['intents',
                             'entities',
                             'metadata',
                             'dialog_nodes',
                             'counterexamples',
                             'system_settings',
                             'learning_opt_out',
                             'name',
                             'language',
                             'description']
        skill_file = os.path.join(tgt_folder, 'skill.json')
        with open(skill_file, 'r', encoding='utf-8') as json_file:
            skill_dict = json.load(json_file)
        skill_dict['learning_opt_out'] = meta['learning_opt_out']
        skill_dict['system_settings'] = meta['system_settings']
        ordered = OrderedDict([(key, skill_dict[key]) for key in preferred_sorting if key in skill_dict])
        with open(skill_file, 'w', encoding='utf-8') as json_file:
            json.dump(ordered, json_file, ensure_ascii=False, indent=2)

    @classmethod
    def _get_skill_meta(cls, full_path: str) -> str:
        with open(full_path, 'r', encoding='utf-8') as json_file:
            cached = json.load(json_file)
            meta = {key: cached[key] for key in ['description',
                                                 'language',
                                                 'learning_opt_out',
                                                 'name',
                                                 'system_settings']}
            return meta

    @classmethod
    def decompose_skill_file(cls, full_path: str, skill_name: str = '') -> bool:
        """
        Decompose a skill with WAW. Use the internal name as the target folder, or the one supplied.
        """
        full_path = os.path.abspath(full_path)
        meta = cls._get_skill_meta(full_path)
        if not skill_name:
            skill_name = meta['name']
        cls._make_decompose_folders(skill_name)
        cls._to_smaller_json_files(full_path, skill_name, meta)
        cls._to_csv_intents(skill_name)
        cls._to_csv_entities(skill_name)
        cls._to_xml_dialog(skill_name)
        return True

    @classmethod
    def decompose_all_skill_files(cls, force) -> bool:
        pattern = os.path.join(cfg.skills_folder(), '*.json')
        for file_path in glob(pattern):
            if not force:
                dir_name = cls._get_skill_meta(file_path)['name']
                dir_name = os.path.join(cfg.WAW_FOLDER, dir_name)
                file_name = os.path.basename(file_path)
                if not click.confirm(f'\nDo you want to use Watson Assistant Workbench\n'
                                     f'to decompose file "{file_name}"\n'
                                     f'into folder "{dir_name}"?',
                                     default=True):
                    continue
            cls.decompose_skill_file(file_path)

    @classmethod
    def reassemble_skill_file(cls,
                              skill_name: str,
                              new_name: str = '',
                              force: bool = False) -> str:
        """
        Assemble the waw/{skill_name}/* files into waw/re-assembled/{new_name}/skill.json
        """
        if not new_name:
            new_name = skill_name
        tgt_folder = cls._make_reassemble_folder(new_name)
        tgt_file = os.path.join(tgt_folder, 'skill.json')
        if os.path.isfile(tgt_file):
            if force or click.confirm('Overwrite existing file?',
                                      abort=True):
                os.remove(tgt_file)

        cls._reassemble_dialog(skill_name, tgt_folder)
        cls._reassemble_entities(skill_name, tgt_folder)
        cls._reassemble_intents(skill_name, tgt_folder)
        cls._reassemble_reassembled_json_files(skill_name, tgt_folder)
        return tgt_file
